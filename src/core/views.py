from django.views.generic import TemplateView

from common.mixins import TitleMixin


class IndexView(TitleMixin, TemplateView):
    template_name: str = "index.html"
    title: str = "Online cryptocurrency exchange - CryptoChicken"


class AMLRulesView(TitleMixin, TemplateView):
    template_name: str = "core/aml.html"
    title: str = "AML rules - CryptoChicken"
