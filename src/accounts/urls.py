from django.urls import path

from accounts.views import (
    UserRegisterView,
    UserLoginView,
    UserLogoutView,
    activate_account_view,
)

app_name = "accounts"

urlpatterns = [
    path("sign-up/", UserRegisterView.as_view(), name="sign-up"),
    path("sign-in/", UserLoginView.as_view(), name="sign-in"),
    path("sign-out/", UserLogoutView.as_view(), name="sign-out"),
    path("activate/<uidb64>/<token>/", activate_account_view, name="activate"),
]
