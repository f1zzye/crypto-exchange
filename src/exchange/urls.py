from django.urls import path
from .views import ExchangeView

app_name: str = "exchange"

urlpatterns = [
    path("exchange/", ExchangeView.as_view(), name="exchange"),
]
