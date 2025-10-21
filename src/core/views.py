from decimal import Decimal
from http import HTTPStatus

import httpx
from django.conf import settings
from django.db import models
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from pytoniq_core import Address

from decouple import config
from common.mixins import TitleMixin
from core.utils.captcha import CaptchaGenerator
from orders.models import ExchangeOrder
from exchange.models.pool import Pool
from exchange.models.token import Token


def tonconnect_manifest(request):

    manifest = {
        "url": settings.NGROK_URL,
        "name": "CryptoChicken Exchange",
        "iconUrl": f"{settings.NGROK_URL}/static/img/ton-connect/logo.png",
        "termsOfUseUrl": f"{settings.NGROK_URL}/tos/",
        "privacyPolicyUrl": f"{settings.NGROK_URL}/privacy/",
    }

    response = JsonResponse(manifest)
    return response


class NetworkConfig:
    MAINNET = "mainnet"
    TESTNET = "testnet"

    CURRENT_NETWORK = config("TON_NETWORK", TESTNET)

    API_URLS = {
        MAINNET: config("TON_MAINNET_API_URL", "https://toncenter.com/api/v2"),
        TESTNET: config("TON_TESTNET_API_URL", "https://testnet.toncenter.com/api/v2"),
    }


@method_decorator(csrf_exempt, name="dispatch")
class WalletTonService(View):
    def get(self, request) -> JsonResponse:
        address = request.GET.get("address")
        network = request.GET.get("network", NetworkConfig.CURRENT_NETWORK)

        if not address:
            return JsonResponse(
                {"error": "No address provided"}, status=HTTPStatus.BAD_REQUEST
            )

        try:
            formatted_address = self._format_address(address, network)
            short_address = self._make_short_address(formatted_address)
            balance = self._get_balance(formatted_address, network)

            return JsonResponse(
                {
                    "balance": balance,
                    "address": formatted_address,
                    "shortAddress": short_address,
                }
            )

        except Exception as e:
            print(f"Error processing wallet: {e}")
            return JsonResponse(
                {
                    "balance": "0 TON",
                    "address": address,
                    "shortAddress": self._make_short_address(address),
                }
            )

    @staticmethod
    def _format_address(address: str, network: str) -> str:
        try:
            addr_obj = Address(address)

            formatted = addr_obj.to_str(
                is_user_friendly=True,
                is_bounceable=False,
                is_url_safe=True,
                is_test_only=(network == NetworkConfig.TESTNET),
            )

            return formatted

        except Exception as e:
            print(f"Address formatting error: {e}")
            return address

    @staticmethod
    def _make_short_address(address: str) -> str:
        if len(address) <= 8:
            return address
        return f"{address[:4]}...{address[-4:]}"

    @staticmethod
    def _format_balance(balance_nano: int) -> str:
        balance_ton = balance_nano / 1e9

        if balance_ton == 0:
            return "0 TON"
        elif balance_ton < 0.01:
            return "< 0.01 TON"
        else:
            return f"{balance_ton:.2f} TON"

    def _get_balance(self, address: str, network: str) -> str:
        try:
            base_url = NetworkConfig.API_URLS.get(
                network, NetworkConfig.API_URLS[NetworkConfig.CURRENT_NETWORK]
            )

            url = f"{base_url}/getAddressBalance?address={address}"

            with httpx.Client(timeout=10.0) as client:
                response = client.get(url)
                response.raise_for_status()
                data = response.json()

            if data.get("ok"):
                balance_nano = int(data.get("result", 0))
                return self._format_balance(balance_nano)

            return "0 TON"

        except Exception as e:
            print(f"Balance fetch error: {e}")
            return "0 TON"


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
        context.update(
            {
                "captcha": captcha_data,
                "tokens": tokens,
            }
        )
        return context

    def post(self, request, *args, **kwargs):
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            action = request.POST.get("action")
            if action == "validate_captcha":
                return self._handle_ajax_captcha_validation(request)
            else:
                return self._handle_ajax_captcha(request)

        return self._handle_form_submission(request)

    def _handle_ajax_captcha_validation(self, request):
        user_answer = request.POST.get("captcha_answer")
        correct_answer = request.session.get("captcha_answer")

        try:
            is_valid = user_answer and int(user_answer) == correct_answer
        except (ValueError, TypeError):
            is_valid = False

        return JsonResponse({"is_valid": is_valid})

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
            return self._render_with_success()
        except Exception as e:
            return self._render_with_error(f"Ошибка создания заявки: {str(e)}")

    @staticmethod
    def _validate_form(request):
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
            "give_token_id": request.POST["give_token_id"],
            "receive_token_id": request.POST["receive_token_id"],
            "give_amount": request.POST["sum1"],
            "receive_amount": request.POST["sum2"],
            "email": request.POST["cf6"],
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

    @staticmethod
    def _find_pool(give_token, receive_token):
        return Pool.objects.filter(
            models.Q(token1=give_token, token2=receive_token)
            | models.Q(token1=receive_token, token2=give_token),
            is_active=True,
        ).first()

    def _render_with_success(self):
        captcha_data = self.captcha.generate()
        self.request.session["captcha_answer"] = captcha_data["result"]

        tokens = (
            Token.objects.filter(is_active=True)
            .select_related("network")
            .order_by("name")
        )

        context = {"captcha": captcha_data, "tokens": tokens, "success": True}
        return render(self.request, self.template_name, context)

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

def get_pool_contract_address(request):
    token1_id = request.GET.get('token1')
    token2_id = request.GET.get('token2')

    if not token1_id or not token2_id:
        return JsonResponse({'contract_address': ''})

    pool = Pool.objects.filter(
        models.Q(token1_id=token1_id, token2_id=token2_id) |
        models.Q(token1_id=token2_id, token2_id=token1_id),
        is_active=True
    ).first()

    return JsonResponse({
        'contract_address': pool.contract_address if pool and pool.contract_address else ''
    })

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
