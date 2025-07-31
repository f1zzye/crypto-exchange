from django.urls import path

from accounts.views import (
    UserRegisterView,
    UserLoginView,
    activate_account_view,
)

app_name = "accounts"

urlpatterns = [
    path("sign-up/", UserRegisterView.as_view(), name="sign-up"),
    path("sign-in/", UserLoginView.as_view(), name="sign-in"),
    path("activate/<uidb64>/<token>/", activate_account_view, name="activate"),
]
