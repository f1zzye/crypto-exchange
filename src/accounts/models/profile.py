from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    avatar = models.ImageField(
        _("avatar"),
        upload_to="avatars/",
        default="avatars/default-avatar.jpg",
        blank=True,
        null=True,
    )

    def __str__(self):
        return f"{self.user}"

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"
