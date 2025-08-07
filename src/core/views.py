from decimal import Decimal

from django.shortcuts import redirect, render
from django.views.generic import TemplateView

from common.mixins import TitleMixin
from core.utils.captcha import CaptchaGenerator

from exchange.models import Token, ExchangeOrder, Pool
from django.db import models
from django.views import View
from django.utils.decorators import method_decorator
from pytoniq_core import Address
import httpx
from http import HTTPStatus

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


def tonconnect_manifest(request):
    manifest = {
        "url": "https://5cc323479e51.ngrok-free.app",
        "name": "CryptoChicken Exchange",
        "iconUrl": "https://5cc323479e51.ngrok-free.app/static/img/logo.png",
        "termsOfUseUrl": "https://5cc323479e51.ngrok-free.app/tos/",
        "privacyPolicyUrl": "https://5cc323479e51.ngrok-free.app/privacy/",
    }

    response = JsonResponse(manifest)
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response["Access-Control-Allow-Headers"] = "Content-Type"
    response["Content-Type"] = "application/json"

    return response


@method_decorator(csrf_exempt, name="dispatch")
class WalletTonService(View):

    def get(self, request) -> JsonResponse:
        address = request.GET["address"]
        if not address:
            return JsonResponse(
                {"error": "No address provided"}, status=HTTPStatus.BAD_REQUEST
            )

        try:
            address_data = self._process_address(address)
            balance = self._get_balance(address_data["user_friendly"])

            return JsonResponse(
                {
                    "balance": balance,
                    "userFriendlyAddress": address_data["user_friendly"],
                    "shortAddress": address_data["short"],
                }
            )

        except ValueError:
            return JsonResponse(
                {
                    "balance": "0.00 TON",
                    "userFriendlyAddress": address,
                    "shortAddress": address,
                }
            )

    @staticmethod
    def _process_address(address: str) -> dict:
        addr_obj = Address(address)
        user_friendly = addr_obj.to_str(
            is_user_friendly=True, is_bounceable=True, is_url_safe=True
        )

        short = (
            f"{user_friendly[:4]}...{user_friendly[-4:]}"
            if len(user_friendly) > 8
            else user_friendly
        )

        return {"user_friendly": user_friendly, "short": short}

    @staticmethod
    def _format_balance(balance_nano: int) -> str:
        balance_ton = balance_nano / 1e9

        if balance_ton == 0:
            return "0$"
        elif balance_ton < 0.01:
            return "< 0.01"
        else:
            return f"{balance_ton:.2f} TON"

    @staticmethod
    def _get_balance(user_friendly_address: str) -> str:
        try:
            url = f"https://toncenter.com/api/v2/getAddressBalance?address={user_friendly_address}"

            with httpx.Client(timeout=10.0) as client:
                response = client.get(url)
                response.raise_for_status()
                data = response.json()

            if data["ok"]:
                balance_nano = int(data["result"])
                return WalletTonService._format_balance(balance_nano)
            else:
                return "0$"

        except (httpx.RequestError, KeyError, ValueError):
            return "0$"


class IndexView(TitleMixin, TemplateView):
    template_name: str = "index.html"
    title: str = "Online cryptocurrency exchange - CryptoChicken"

    def dispatch(self, request, *args, **kwargs):
        self.captcha = CaptchaGenerator()
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        captcha_data = self.captcha.generate()

        self.request.session["captcha_answer"] = captcha_data["result"]

        tokens = (
            Token.objects.filter(is_active=True)
            .select_related("network")
            .order_by("name")
        )

        context.update({"captcha": captcha_data, "tokens": tokens})
        return context

    def post(self, request, *args, **kwargs):
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return self._handle_ajax_captcha(request)

        return self._handle_form_submission(request)

    def _handle_ajax_captcha(self, request):
        captcha_data = self.captcha.generate()
        request.session["captcha_answer"] = captcha_data["result"]
        return JsonResponse(captcha_data)

    def _handle_form_submission(self, request):
        validation_error = self._validate_form(request)
        if validation_error:
            return self._render_with_error(validation_error)

        try:
            order = self._create_exchange_order(request)
            request.session["order_id"] = str(order.id)
            return redirect("exchange:order_success")
        except Exception as e:
            return self._render_with_error(f"Ошибка создания заявки: {str(e)}")

    def _validate_form(self, request):
        if not all([request.POST.get("check_rule"), request.POST.get("add_rules")]):
            return "Необходимо согласиться с условиями"

        user_answer = request.POST.get("number")
        correct_answer = request.session.get("captcha_answer")

        try:
            if not user_answer or int(user_answer) != correct_answer:
                raise ValueError()
        except (ValueError, TypeError):
            return "Неверный ответ на капчу"

        required_fields = [
            "give_token_id",
            "receive_token_id",
            "sum1",
            "sum2",
            "cf6",
        ]
        if not all(request.POST.get(field) for field in required_fields):
            return "Заполните все обязательные поля"

        return None

    def _create_exchange_order(self, request):
        form_data = {
            "give_token_id": request.POST.get("give_token_id"),
            "receive_token_id": request.POST.get("receive_token_id"),
            "give_amount": request.POST.get("sum1"),
            "receive_amount": request.POST.get("sum2"),
            "email": request.POST.get("cf6"),
        }

        give_token = Token.objects.get(id=form_data["give_token_id"], is_active=True)
        receive_token = Token.objects.get(
            id=form_data["receive_token_id"], is_active=True
        )

        pool = self._find_pool(give_token, receive_token)
        if not pool:
            raise ValueError(
                f"Пул для пары {give_token.short_name}/{receive_token.short_name} не найден"
            )

        give_amount = Decimal(str(form_data["give_amount"]))
        receive_amount = Decimal(str(form_data["receive_amount"]))
        exchange_rate = (
            receive_amount / give_amount if give_amount > 0 else Decimal("0")
        )

        return ExchangeOrder.objects.create(
            email=form_data["email"],
            give_token=give_token,
            give_amount=give_amount,
            receive_token=receive_token,
            receive_amount=receive_amount,
            exchange_rate=exchange_rate,
            fee_percentage=pool.fee_percentage,
            pool=pool,
            status="pending",
        )

    def _find_pool(self, give_token, receive_token):
        return Pool.objects.filter(
            models.Q(token1=give_token, token2=receive_token)
            | models.Q(token1=receive_token, token2=give_token),
            is_active=True,
        ).first()

    def _render_with_error(self, error_message):
        captcha_data = self.captcha.generate()
        self.request.session["captcha_answer"] = captcha_data["result"]

        tokens = (
            Token.objects.filter(is_active=True)
            .select_related("network")
            .order_by("name")
        )

        context = {"captcha": captcha_data, "tokens": tokens, "error": error_message}
        return render(self.request, self.template_name, context)


class AMLRulesView(TitleMixin, TemplateView):
    template_name: str = "core/aml.html"
    title: str = "AML rules - CryptoChicken"


class RaffleView(TitleMixin, TemplateView):
    template_name: str = "core/raffle.html"
    title: str = "Raffle"


class CashbackInfoView(TitleMixin, TemplateView):
    template_name: str = "core/cashback-info.html"
    title: str = "Cashback - CryptoChicken"


class DepositView(TitleMixin, TemplateView):
    template_name: str = "core/deposit.html"
    title: str = "Deposit - CryptoChicken"
