import os

from .base import *

INSTALLED_APPS.append("dev")

# Django test always makes DEBUG False
DEBUG = False

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "sqlite3.db"
    }
}

# It's needed for django-coverage-plugin
TEMPLATES[0]["OPTIONS"]["debug"] = True

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher"
]

CHANNEL_LAYERS = {
    'default': {
        "BACKEND": "channels.layers.InMemoryChannelLayer"
    },
}

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

# It's needed to test routing
ALLOWED_HOSTS = ["*"]

FS_REDIS_DB = 1
