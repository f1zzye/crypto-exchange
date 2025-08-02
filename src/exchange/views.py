from django.shortcuts import render
from django.views import View

from .models import Token


class ExchangeView(View):
    def get(self, request):
        tokens = (
            Token.objects.filter(is_active=True)
            .select_related("network")
            .order_by("name")
        )

        context = {"tokens": tokens}

        return render(request, "index.html", context)
