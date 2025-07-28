from django.views.generic import TemplateView

from common.mixins import TitleMixin


class IndexView(TitleMixin, TemplateView):
    template_name = "index.html"
    title = "Online cryptocurrency exchange - CryptoChicken"