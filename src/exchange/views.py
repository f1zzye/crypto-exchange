import json
from decimal import Decimal
from common.mixins import TitleMixin
from django.http import JsonResponse
from django.views.generic import TemplateView
from exchange.models import Token, ExchangeOrder, Pool
from django.db import models
from .models import Token, Pool


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


def calculate_exchange_api(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Method not allowed"})

    try:
        data = json.loads(request.body)
        give_token_id = data.get("give_token_id")
        receive_token_id = data.get("receive_token_id")
        amount = data.get("amount", 0)

        if not give_token_id or not receive_token_id:
            return JsonResponse({"success": False, "error": "Токены не выбраны"})

        if give_token_id == receive_token_id:
            return JsonResponse({"success": False, "error": "Выберите разные токены"})

        if not amount or float(amount) <= 0:
            return JsonResponse(
                {"success": True, "output_amount": "0", "effective_rate": "0"}
            )

        amount = Decimal(str(amount))

        give_token = Token.objects.get(id=give_token_id, is_active=True)
        receive_token = Token.objects.get(id=receive_token_id, is_active=True)

        pool = Pool.objects.filter(
            models.Q(token1=give_token, token2=receive_token)
            | models.Q(token1=receive_token, token2=give_token),
            is_active=True,
        ).first()

        if not pool:
            return JsonResponse(
                {
                    "success": False,
                    "error": f"Пул {give_token.short_name}/{receive_token.short_name} не найден",
                }
            )

        output_amount = pool.get_output_amount(give_token, amount)
        effective_rate = output_amount / amount if amount > 0 else Decimal("0")

        return JsonResponse(
            {
                "success": True,
                "output_amount": str(output_amount),
                "effective_rate": str(effective_rate),
                "give_token_name": give_token.short_name,
                "receive_token_name": receive_token.short_name,
                "fee_percentage": str(pool.fee_percentage),
            }
        )

    except Token.DoesNotExist:
        return JsonResponse({"success": False, "error": "Токен не найден"})
    except Exception as e:
        return JsonResponse({"success": False, "error": f"Ошибка: {str(e)}"})
