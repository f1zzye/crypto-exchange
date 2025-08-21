from pathlib import Path

from decouple import config
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

BASE_DIR = Path(__file__).resolve().parent.parent.parent


INSTALLED_APPS: list[str] = [
    # Django apps
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "unfold.contrib.inlines",
    "unfold.contrib.import_export",
    "unfold.contrib.guardian",
    "unfold.contrib.simple_history",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Custom apps
    # My apps
    "core",
    "accounts",
    "exchange",
]

MIDDLEWARE: list[str] = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF: str = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION: str = "config.wsgi.application"


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGES = [
    ("uk", _("Ukrainian")),
    ("en", _("English")),
]

LANGUAGE_CODE: str = "uk"

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

TIME_ZONE: str = "UTC"

USE_I18N: bool = True

USE_TZ: bool = True


STATIC_URL: str = "/static/"

STATICFILES_DIRS = [BASE_DIR / "static"]  # noqa

MEDIA_URL: str = "/media/"

MEDIA_ROOT = BASE_DIR / "media"  # noqa

STATIC_ROOT = BASE_DIR / "staticfiles"  # noqa


DEFAULT_AUTO_FIELD: str = "django.db.models.BigAutoField"

AUTHENTICATION_BACKENDS = ("django.contrib.auth.backends.ModelBackend",)

AUTH_USER_MODEL: str = "accounts.User"

LOGIN_URL: str = "accounts:sign-in"

LOGIN_REDIRECT_URL: str = "core:index"
LOGOUT_REDIRECT_URL: str = "core:index"

SESSION_COOKIE_AGE: int = 86400


UNFOLD = {
    "SITE_TITLE": "Admin Dashboard",
    "SITE_HEADER": "Admin Dashboard - Crypto Exchange",
    "SITE_FOOTER": "Crypto Exchange Admin",
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": [
            {
                "title": _("Navigation"),
                "separator": True,
                "items": [
                    {
                        "title": _("Dashboard"),
                        "icon": "dashboard",
                        "link": reverse_lazy("admin:index"),
                    },
                ],
            },
            {
                "title": _("Blockchain"),
                "separator": True,
                "items": [
                    {
                        "title": _("Pools"),
                        "icon": "circle",
                        "link": reverse_lazy("admin:exchange_pool_changelist"),
                    },
                    {
                        "title": _("Networks"),
                        "icon": "hub",
                        "link": reverse_lazy("admin:exchange_network_changelist"),
                    },
                    {
                        "title": _("Tokens"),
                        "icon": "token",
                        "link": reverse_lazy("admin:exchange_token_changelist"),
                    },
                    {
                        "title": _("Exchange Orders "),
                        "icon": "swap_horiz",
                        "link": reverse_lazy("admin:exchange_exchangeorder_changelist"),
                    },
                ],
            },
            {
                "title": _("Users"),
                "separator": True,
                "items": [
                    {
                        "title": _("Users"),
                        "icon": "person",
                        "link": reverse_lazy("admin:accounts_user_changelist"),
                    },
                ],
            },
        ],
    },
}

NODEJS_API_URL = config("NODEJS_API_URL", default="http://localhost:3000")

DEFAULT_ADMIN_WALLET = config(
    "DEFAULT_ADMIN_WALLET", default="EQB6B3_azSTKuDr9999999999Q0jg48PzfYiLLv_wCYBGwcR"
)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": "pool_deployments.log",
        },
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "pools.signals": {
            "handlers": ["file", "console"],
            "level": "INFO",
            "propagate": True,
        },
    },
}
