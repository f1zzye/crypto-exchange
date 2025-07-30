from config.settings.base import *

DEBUG = True

SECRET_KEY = "django-insecure-hn^ppv^_puys)su29!vf@3_w9d(6c6_phprp03-x*eru$@%5hz"

ALLOWED_HOSTS = ["*", "localhost"]


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

STATIC_URL = "/static/"
