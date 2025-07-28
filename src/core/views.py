from django.views.generic import TemplateView

from common.mixins import TitleMixin


class IndexView(TitleMixin, TemplateView):
    template_name = "core/index.html"
    title = "Index"