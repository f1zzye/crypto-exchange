from django.urls import path

from core.views import IndexView, AMLRulesView, RaffleView, CashbackInfoView, DepositView

app_name: str = "core"

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path("aml/", AMLRulesView.as_view(), name="aml"),
    path("raffle/", RaffleView.as_view(), name="raffle"),
    path("cashback-info/", CashbackInfoView.as_view(), name="cashback"),
    path("deposit/", DepositView.as_view(), name="deposit"),
]
