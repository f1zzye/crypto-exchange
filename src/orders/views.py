from django.views.generic import TemplateView

from common.mixins import TitleMixin

from .models import ExchangeOrder


class OrderCreateView(TitleMixin, TemplateView):
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
