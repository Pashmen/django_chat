from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


SECRET_KEY = "a+2@0$&ybly8$$6b#i$+-(t2kmxq0qnorhsgylbh@!-*bg*=&p"
DEBUG = True
ALLOWED_HOSTS = []


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "channels",

    "messages",
    "common",
    "dev"
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "sqlite3.db"
    }
}

AUTH_USER_MODEL = "common.CustomUser"
ROOT_URLCONF = "common.urls"

ASGI_APPLICATION = "config.asgi.application"

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer"
    },
}

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Europe/Moscow"

USE_I18N = True
USE_TZ = True

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "dialogs"
LOGOUT_REDIRECT_URL = "login"

STATIC_URL = "static/"

FS_MAX_MESSAGE_LENGTH = 400
FS_DIALOG_INTEGRITY_TIMEOUT = 20*60
FS_DIALOGS_INTEGRITY_TIMEOUT = 20*60
FS_UNREAD_DIALOGS_TIMEOUT = 20*60
FS_NEW_MESSAGES_PERIOD = 60*60
FS_REDIS_DB = 0

FS_TIME_FORMAT = "%Y.%m.%d %H:%M:%S"
