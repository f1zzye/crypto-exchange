from config.settings.base import * # noqa


DEBUG: bool = True

SECRET_KEY: str = "django-insecure-hn^ppv^_puys)su29!vf@3_w9d(6c6_phprp03-x*eru$@%5hz"

ALLOWED_HOSTS: list[str] = ["*", "localhost", "127.0.0.1"]


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

STATIC_URL: str = "/static/"