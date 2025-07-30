from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import Profile
from django.utils.translation import gettext_lazy as _


class ProfileAdmin(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = "Profiles"

@admin.register(get_user_model())
class UserAdmin(admin.ModelAdmin):
    inlines = [ProfileAdmin]
    list_display = (
        "email",
        "username",
        "is_active",
        "is_staff",
        "date_joined",
    )
    list_display_links = ("email", "username")
    search_fields = ("email", "username")
    ordering = ("-date_joined", "email")
    readonly_fields = ("date_joined",)
    fieldsets = (
        (_("Authentication"), {"fields": ("email", "username", "password")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (
            _("Important Dates"),
            {
                "fields": ("last_login", "date_joined"),
            },
        ),
    )
