from django.urls import path

from accounts.views import (
    UserRegisterView,
    activate_account_view,
)

app_name = "accounts"

urlpatterns = [
    path("sign-up/", UserRegisterView.as_view(), name="sign-up"),
    path("activate/<uidb64>/<token>/", activate_account_view, name="activate"),
]
