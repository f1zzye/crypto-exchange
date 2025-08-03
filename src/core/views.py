from decimal import Decimal

from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.generic import TemplateView

from common.mixins import TitleMixin
from core.utils.captcha import CaptchaGenerator

from exchange.models import Token, ExchangeOrder, Pool
from django.db import models


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

        context["captcha"] = captcha_data
        context["tokens"] = tokens
        return context

    def post(self, request, *args, **kwargs):
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            captcha_data = self.captcha.generate()
            request.session["captcha_answer"] = captcha_data["result"]
            return JsonResponse(captcha_data)

        # Получаем данные формы
        check_rule = request.POST.get("check_rule")
        add_rules = request.POST.get("add_rules")
        user_answer = request.POST.get("number")
        correct_answer = request.session.get("captcha_answer")

        # Данные обмена
        give_token_id = request.POST.get("give_token_id")
        receive_token_id = request.POST.get("receive_token_id")
        give_amount = request.POST.get("sum1")
        receive_amount = request.POST.get("sum2")

        # Данные пользователя
        email = request.POST.get("cf6")
        wallet_address = request.POST.get("account2")

        # Базовые проверки
        if not check_rule or not add_rules:
            captcha_data = self.captcha.generate()
            request.session["captcha_answer"] = captcha_data["result"]

            context = self.get_context_data()
            context["captcha"] = captcha_data
            context["error"] = "Необходимо согласиться с условиями"
            return render(request, self.template_name, context)

        # Проверка капчи
        try:
            if not user_answer or int(user_answer) != correct_answer:
                raise ValueError()
        except (ValueError, TypeError):
            captcha_data = self.captcha.generate()
            request.session["captcha_answer"] = captcha_data["result"]

            context = self.get_context_data()
            context["captcha"] = captcha_data
            context["error"] = "Неверный ответ на капчу"
            return render(request, self.template_name, context)

        # Проверка данных обмена
        if not all(
            [
                give_token_id,
                receive_token_id,
                give_amount,
                receive_amount,
                email,
                wallet_address,
            ]
        ):
            captcha_data = self.captcha.generate()
            request.session["captcha_answer"] = captcha_data["result"]

            context = self.get_context_data()
            context["captcha"] = captcha_data
            context["error"] = "Заполните все обязательные поля"
            return render(request, self.template_name, context)

        try:
            # Создаем заявку на обмен
            order = self.create_exchange_order(
                give_token_id,
                receive_token_id,
                give_amount,
                receive_amount,
                email,
                wallet_address,
            )

            # Сохраняем ID заявки в сессии
            request.session["order_id"] = str(order.id)

            # Редиректим на страницу успеха
            return redirect("core:order_success")

        except Exception as e:
            captcha_data = self.captcha.generate()
            request.session["captcha_answer"] = captcha_data["result"]

            context = self.get_context_data()
            context["captcha"] = captcha_data
            context["error"] = f"Ошибка создания заявки: {str(e)}"
            return render(request, self.template_name, context)

    def create_exchange_order(
        self,
        give_token_id,
        receive_token_id,
        give_amount,
        receive_amount,
        email,
        wallet_address,
    ):
        """Создает заявку на обмен"""

        # Получаем токены
        give_token = Token.objects.get(id=give_token_id, is_active=True)
        receive_token = Token.objects.get(id=receive_token_id, is_active=True)

        # Ищем пул
        pool = Pool.objects.filter(
            models.Q(token1=give_token, token2=receive_token)
            | models.Q(token1=receive_token, token2=give_token),
            is_active=True,
        ).first()

        if not pool:
            raise ValueError(
                f"Пул для пары {give_token.short_name}/{receive_token.short_name} не найден"
            )

        # Преобразуем в Decimal
        give_amount_decimal = Decimal(str(give_amount))
        receive_amount_decimal = Decimal(str(receive_amount))

        # Рассчитываем курс
        exchange_rate = (
            receive_amount_decimal / give_amount_decimal
            if give_amount_decimal > 0
            else Decimal("0")
        )

        # Создаем заявку
        order = ExchangeOrder.objects.create(
            email=email,
            wallet_address=wallet_address,
            give_token=give_token,
            give_amount=give_amount_decimal,
            receive_token=receive_token,
            receive_amount=receive_amount_decimal,
            exchange_rate=exchange_rate,
            fee_percentage=pool.fee_percentage,
            pool=pool,
            status="pending",
        )

        return order


class OrderSuccessView(TitleMixin, TemplateView):
    template_name: str = "exchange/order_success.html"
    title: str = "Заявка создана - CryptoChicken"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        order_id = self.request.session.get("order_id")
        if order_id:
            try:
                order = ExchangeOrder.objects.get(id=order_id)
                context["order"] = order
            except ExchangeOrder.DoesNotExist:
                pass

        return context


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
