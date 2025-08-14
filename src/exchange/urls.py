from django.urls import path

from exchange.views import OrderSuccessView, calculate_exchange_api

app_name: str = "exchange"

urlpatterns = [
    path("calculate-exchange/", calculate_exchange_api, name="calculate_exchange_api"),
    path("order-success/", OrderSuccessView.as_view(), name="order_success"),
]
