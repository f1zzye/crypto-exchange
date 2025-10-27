from decouple import config

from config.settings.base import *  # noqa

DEBUG: bool = True

SECRET_KEY: str = "django-insecure-hn^ppv^_puys)su29!vf@3_w9d(6c6_phprp03-x*eru$@%5hz"

ALLOWED_HOSTS: list[str] = [
    "*",
]

CORS_ALLOW_ALL_ORIGINS: bool = True
CORS_ALLOW_CREDENTIALS: bool = True

CORS_ALLOW_HEADERS = [
    "authorization",
    "content-type",
    "accept",
]

CSRF_TRUSTED_ORIGINS = [
    "https://*.ngrok.io",
    "https://*.ngrok-free.app",
    "https://*.ngrok-free.dev",
    "https://e5febd957294.ngrok-free.app",
]

CORS_ALLOWED_ORIGINS: list[str] = [
    "https://e5febd957294.ngrok-free.app",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

STATIC_URL = "/static/"

STATICFILES_DIRS = [BASE_DIR / "static"]  # noqa

MEDIA_URL = "/media/"

MEDIA_ROOT = BASE_DIR / "media"  # noqa

STATIC_ROOT = BASE_DIR / "staticfiles"  # noqa


EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_USE_TLS = True
EMAIL_HOST = "smtp.gmail.com"
EMAIL_HOST_USER = config("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD")
EMAIL_PORT = 587
EMAIL_FAIL_SILENTLY = False

NGROK_URL = config("NGROK_URL")
