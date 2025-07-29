from django.urls import path

from core.views import IndexView, AMLRulesView

app_name: str = "core"

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path("aml/", AMLRulesView.as_view(), name="aml"),
]