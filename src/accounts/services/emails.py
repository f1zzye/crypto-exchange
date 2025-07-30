from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage, send_mail
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.translation import gettext_lazy as _


def send_confirmation_email(request, user):
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    current_site = get_current_site(request)
    mail_subject = _("Confirm your email address for CryptoChicken")
    message = render_to_string(
        "emails/registration_email.html",
        {
            "user": user,
            "domain": current_site.domain,
            "uid": uid,
            "token": token,
        },
    )

    email = EmailMessage(
        subject=mail_subject,
        body=message,
        from_email=settings.EMAIL_HOST_USER,
        to=[user.email],
    )
    email.content_subtype = "html"
    email.send()


# def send_password_reset_email(request, user):
#     token = default_token_generator.make_token(user)
#     uid = urlsafe_base64_encode(force_bytes(user.pk))
#     current_site = get_current_site(request)
#     mail_subject = _("Reset password for CryptoChicken")
#     message = render_to_string(
#         "emails/password_reset_email.html",
#         {
#             "user": user,
#             "domain": current_site.domain,
#             "uid": uid,
#             "token": token,
#         },
#     )
#
#     email = EmailMessage(
#         subject=mail_subject,
#         body=message,
#         from_email=settings.EMAIL_HOST_USER,
#         to=[user.email],
#     )
#     email.content_subtype = "html"
#     email.send()
#
#     success_message = _(
#         "We have sent you instructions by email to recover your password."
#     )
#     return reverse_lazy("core:index"), success_message
