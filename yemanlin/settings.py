from pathlib import Path


# =========================================================
# BASE
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent


# =========================================================
# SÉCURITÉ
# =========================================================

SECRET_KEY = "CHANGE-ME-IN-PRODUCTION"

# En développement local
DEBUG = True

ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
]


# =========================================================
# APPLICATIONS
# =========================================================

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "store",
]


# =========================================================
# MIDDLEWARE
# =========================================================

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",

    "django.middleware.common.CommonMiddleware",

    "django.middleware.csrf.CsrfViewMiddleware",

    "django.contrib.auth.middleware.AuthenticationMiddleware",

    "django.contrib.messages.middleware.MessageMiddleware",
]


# =========================================================
# URL
# =========================================================

ROOT_URLCONF = "yemanlin.urls"


# =========================================================
# TEMPLATES
# =========================================================

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",

        "DIRS": [
            BASE_DIR / "templates",
        ],

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


# =========================================================
# WSGI
# =========================================================

WSGI_APPLICATION = "yemanlin.wsgi.application"


# =========================================================
# DATABASE
# =========================================================

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# =========================================================
# AUTHENTIFICATION
# =========================================================

AUTH_PASSWORD_VALIDATORS = []

LOGIN_URL = "/admin/login/"

LOGIN_REDIRECT_URL = "/admin/dashboard/"

LOGOUT_REDIRECT_URL = "/admin/login/"


# =========================================================
# LANGUE / TEMPS
# =========================================================

LANGUAGE_CODE = "fr-fr"

TIME_ZONE = "Africa/Porto-Novo"

USE_I18N = True

USE_TZ = True


# =========================================================
# FICHIERS STATIQUES
# =========================================================

STATIC_URL = "/static/"

STATICFILES_DIRS = [
    BASE_DIR / "static",
]


# =========================================================
# FICHIERS MÉDIA
# =========================================================

MEDIA_URL = "/media/"

# Stockage dans l'espace privé de Termux.
# Évite le problème de verrouillage rencontré
# avec /storage/emulated/0/1/media.

MEDIA_ROOT = Path.home() / "yemalin_media"


# =========================================================
# STOCKAGE DJANGO 6
# =========================================================

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },

    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}


# =========================================================
# DJANGO
# =========================================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"