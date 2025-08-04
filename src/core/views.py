from decimal import Decimal

from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.generic import TemplateView

from common.mixins import TitleMixin
from core.utils.captcha import CaptchaGenerator

from exchange.models import Token, ExchangeOrder, Pool
from django.db import models


def tonconnect_manifest(request):
    manifest = {
        "url": "https://7dc4e007bbdd.ngrok-free.app",
        "name": "CryptoChicken Exchange",
        "iconUrl": "https://7dc4e007bbdd.ngrok-free.app/static/img/logo.png",
        "termsOfUseUrl": "https://7dc4e007bbdd.ngrok-free.app/tos/",
        "privacyPolicyUrl": "https://7dc4e007bbdd.ngrok-free.app/privacy/"
    }

    response = JsonResponse(manifest)
    response['Access-Control-Allow-Origin'] = '*'
    response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
    response['Access-Control-Allow-Headers'] = 'Content-Type'
    response['Content-Type'] = 'application/json'

    return response


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
