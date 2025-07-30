from config.settings.base import *  # noqa
from decouple import config

DEBUG: bool = True

SECRET_KEY: str = "django-insecure-hn^ppv^_puys)su29!vf@3_w9d(6c6_phprp03-x*eru$@%5hz"

ALLOWED_HOSTS: list[str] = ["*", "localhost", "127.0.0.1"]


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