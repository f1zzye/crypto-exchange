from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.generic import TemplateView

from common.mixins import TitleMixin
from core.utils.captcha import CaptchaGenerator

from exchange.models import Token


class IndexView(TitleMixin, TemplateView):
    template_name: str = "index.html"
    title: str = "Online cryptocurrency exchange - CryptoChicken"

    def dispatch(self, request, *args, **kwargs):
        self.captcha = CaptchaGenerator()
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        captcha_data = self.captcha.generate()

        self.request.session["captcha_answer"] = captcha_data["result"]

        tokens = (
            Token.objects.filter(is_active=True)
            .select_related("network")
            .order_by("name")
        )

        context["captcha"] = captcha_data
        context["tokens"] = tokens
        return context

    def post(self, request, *args, **kwargs):
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            captcha_data = self.captcha.generate()
            request.session["captcha_answer"] = captcha_data["result"]
            return JsonResponse(captcha_data)

        check_rule = request.POST.get("check_rule")
        add_rules = request.POST.get("add_rules")
        user_answer = request.POST.get("number")
        correct_answer = request.session.get("captcha_answer")

        if not check_rule or not add_rules:
            captcha_data = self.captcha.generate()
            request.session["captcha_answer"] = captcha_data["result"]

            context = self.get_context_data()
            context["captcha"] = captcha_data
            context["error"] = "Please agree to the rules and add them"
            return render(request, self.template_name, context)

        try:
            if not user_answer or int(user_answer) != correct_answer:
                raise ValueError()
        except (ValueError, TypeError):
            captcha_data = self.captcha.generate()
            request.session["captcha_answer"] = captcha_data["result"]

            context = self.get_context_data()
            context["captcha"] = captcha_data
            context["error"] = "Incorrect answer to the captcha"
            return render(request, self.template_name, context)

        return redirect("core:aml")


class AMLRulesView(TitleMixin, TemplateView):
    template_name: str = "core/aml.html"
    title: str = "AML rules - CryptoChicken"


class RaffleView(TitleMixin, TemplateView):
    template_name: str = "core/raffle.html"
    title: str = "Raffle"


class CashbackInfoView(TitleMixin, TemplateView):
    template_name: str = "core/cashback-info.html"
    title: str = "Cashback - CryptoChicken"


class DepositView(TitleMixin, TemplateView):
    template_name: str = "core/deposit.html"
    title: str = "Deposit - CryptoChicken"
