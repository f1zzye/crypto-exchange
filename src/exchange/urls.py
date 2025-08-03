from django.urls import path
from .views import calculate_exchange_api

app_name: str = "exchange"

urlpatterns = [
    path("calculate-exchange/", calculate_exchange_api, name="calculate_exchange_api"),
]
