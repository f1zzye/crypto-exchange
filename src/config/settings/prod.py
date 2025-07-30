from config.settings.base import *


DEBUG: bool = False

SECRET_KEY: str = "django-insecure-!@#%$^&*()_+1234567890-=qwertyuiopasdfghjklzxcvbnm"

ALLOWED_HOSTS: list[str] = ["*", "localhost"]


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

STATIC_URL: str = "/static/"
