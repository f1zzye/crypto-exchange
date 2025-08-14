from django.urls import path

from core.views import (AMLRulesView, CashbackInfoView, DepositView, IndexView,
                        RaffleView, WalletTonService, tonconnect_manifest)

app_name: str = "core"

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path("aml/", AMLRulesView.as_view(), name="aml"),
    path("raffle/", RaffleView.as_view(), name="raffle"),
    path("cashback-info/", CashbackInfoView.as_view(), name="cashback"),
    path("deposit/", DepositView.as_view(), name="deposit"),
    path("tonconnect-manifest.json", tonconnect_manifest, name="tonconnect_manifest"),
    path("api/wallet-balance/", WalletTonService.as_view(), name="wallet_balance"),
]
