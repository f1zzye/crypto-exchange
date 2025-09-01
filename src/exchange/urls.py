from django.urls import path

from exchange.views import calculate_exchange_api
from exchange.admin.admin_views import pool_custom_action

app_name: str = "exchange"

urlpatterns = [
    path("calculate-exchange/", calculate_exchange_api, name="calculate_exchange_api"),
    path(
        "admin/exchange/pool/deploy_contract/",
        pool_custom_action,
        name="pool_custom_action",
    ),
]
