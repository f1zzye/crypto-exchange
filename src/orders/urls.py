from django.urls import path

from orders.views import OrderCreateView

app_name: str = "orders"

urlpatterns = [
    path("order-create/", OrderCreateView.as_view(), name="order_success"),
]
