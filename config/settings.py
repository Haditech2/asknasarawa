"""Settings for the Tambayi Nasarawa project.

Production values are read from environment variables. SQLite and a development
secret are permitted only while DEBUG is enabled so a new contributor can run
the project without a PostgreSQL server.
"""
from __future__ import annotations

import os
from urllib.parse import parse_qs, unquote, urlparse
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: str = "") -> list[str]:
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]


DEBUG = env_bool("DJANGO_DEBUG", True)
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "")
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "django-insecure-development-only-change-me"
    else:
        raise ImproperlyConfigured("DJANGO_SECRET_KEY must be set when DEBUG=False.")

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")
for vercel_host in (
    "asknasarawa.vercel.app",
    os.getenv("VERCEL_URL", ""),
    os.getenv("VERCEL_PROJECT_PRODUCTION_URL", ""),
):
    if vercel_host and vercel_host not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(vercel_host)

CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS")
for vercel_host in (
    "asknasarawa.vercel.app",
    os.getenv("VERCEL_URL", ""),
    os.getenv("VERCEL_PROJECT_PRODUCTION_URL", ""),
):
    if vercel_host:
        vercel_origin = f"https://{vercel_host}"
        if vercel_origin not in CSRF_TRUSTED_ORIGINS:
            CSRF_TRUSTED_ORIGINS.append(vercel_origin)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "apps.accounts.apps.AccountsConfig",
    "apps.core.apps.CoreConfig",
    "apps.faq.apps.FaqConfig",
    "apps.chatbot.apps.ChatbotConfig",
    "apps.analytics.apps.AnalyticsConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.core.middleware.SecurityHeadersMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

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
                "apps.core.context_processors.site_context",
            ],
        },
    },
]

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
DB_ENGINE = os.getenv("DB_ENGINE", "sqlite").strip().lower()
if DATABASE_URL:
    database_url = urlparse(DATABASE_URL)
    if database_url.scheme not in {"postgres", "postgresql"}:
        raise ImproperlyConfigured("DATABASE_URL must use the postgres:// or postgresql:// scheme.")
    database_query = parse_qs(database_url.query)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": unquote(database_url.path.lstrip("/")),
            "USER": unquote(database_url.username or ""),
            "PASSWORD": unquote(database_url.password or ""),
            "HOST": database_url.hostname or "",
            "PORT": str(database_url.port or 5432),
            "CONN_MAX_AGE": int(os.getenv("DB_CONN_MAX_AGE", "60")),
            "OPTIONS": {
                "sslmode": database_query.get("sslmode", [os.getenv("DB_SSLMODE", "require")])[0],
                **(
                    {"channel_binding": database_query["channel_binding"][0]}
                    if "channel_binding" in database_query
                    else {}
                ),
            },
        }
    }
elif DB_ENGINE in {"postgres", "postgresql", "psql"}:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("DB_NAME", "nasarawa_chatbot"),
            "USER": os.getenv("DB_USER", "nasarawa_chatbot"),
            "PASSWORD": os.getenv("DB_PASSWORD", ""),
            "HOST": os.getenv("DB_HOST", "127.0.0.1"),
            "PORT": os.getenv("DB_PORT", "5432"),
            "CONN_MAX_AGE": int(os.getenv("DB_CONN_MAX_AGE", "60")),
            "OPTIONS": {"sslmode": os.getenv("DB_SSLMODE", "prefer")},
        }
    }
else:
    if not DEBUG and os.getenv("DJANGO_ALLOW_SQLITE_IN_PRODUCTION") != "True":
        raise ImproperlyConfigured("PostgreSQL is required when DEBUG=False.")
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en"
LANGUAGES = [("en", "English"), ("ha", "Hausa")]
TIME_ZONE = "Africa/Lagos"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
        if not DEBUG
        else "django.contrib.staticfiles.storage.StaticFilesStorage"
    },
}
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "dashboard:index"
LOGOUT_REDIRECT_URL = "core:home"

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = env_bool("DJANGO_SECURE_COOKIES", not DEBUG)
SESSION_COOKIE_AGE = 60 * 60 * 24 * 14
CSRF_COOKIE_SECURE = env_bool("DJANGO_SECURE_COOKIES", not DEBUG)
CSRF_COOKIE_SAMESITE = "Lax"
SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", not DEBUG)
SECURE_HSTS_SECONDS = int(os.getenv("DJANGO_HSTS_SECONDS", "0" if DEBUG else "31536000"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        *( ["rest_framework.renderers.BrowsableAPIRenderer"] if DEBUG else [] ),
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "120/hour",
        "user": "1000/hour",
        "chat": os.getenv("CHAT_RATE", "30/minute"),
        "faq_search": os.getenv("FAQ_SEARCH_RATE", "60/minute"),
    },
    "EXCEPTION_HANDLER": "apps.core.api.exception_handler",
}

SITE_NAME = "Tambayi Nasarawa"
OFFICIAL_ENQUIRY_EMAIL = os.getenv("OFFICIAL_ENQUIRY_EMAIL", "").strip()
OFFICIAL_ENQUIRY_URL = os.getenv("OFFICIAL_ENQUIRY_URL", "").strip()
CHAT_DATA_RETENTION_DAYS = int(os.getenv("CHAT_DATA_RETENTION_DAYS", "90"))
CHAT_MATCH_THRESHOLD = float(os.getenv("CHAT_MATCH_THRESHOLD", "62"))
CHAT_SUGGESTION_THRESHOLD = float(os.getenv("CHAT_SUGGESTION_THRESHOLD", "35"))

CACHE_BACKEND = os.getenv("CACHE_BACKEND", "local").lower()
if CACHE_BACKEND == "redis" and os.getenv("REDIS_URL"):
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": os.environ["REDIS_URL"],
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "tambayi-nasarawa",
        }
    }

LOG_LEVEL = os.getenv("DJANGO_LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("DJANGO_LOG_FILE", "").strip()
LOG_HANDLERS: list[str] = ["console"]
LOGGING_HANDLERS: dict[str, dict] = {
    "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
}
if LOG_FILE:
    Path(LOG_FILE).parent.mkdir(parents=True, exist_ok=True)
    LOG_HANDLERS.append("file")
    LOGGING_HANDLERS["file"] = {
        "class": "logging.handlers.RotatingFileHandler",
        "filename": LOG_FILE,
        "maxBytes": 10 * 1024 * 1024,
        "backupCount": 5,
        "formatter": "verbose",
    }

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "{levelname} {asctime} {name} {message}", "style": "{"},
    },
    "handlers": LOGGING_HANDLERS,
    "root": {"handlers": LOG_HANDLERS, "level": LOG_LEVEL},
    "loggers": {
        "django.security": {"handlers": LOG_HANDLERS, "level": "WARNING", "propagate": False},
        "apps": {"handlers": LOG_HANDLERS, "level": LOG_LEVEL, "propagate": False},
    },
}

SENTRY_DSN = os.getenv("SENTRY_DSN", "").strip()
if SENTRY_DSN:
    import sentry_sdk

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        send_default_pii=False,
        traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.05")),
        environment=os.getenv("SENTRY_ENVIRONMENT", "production" if not DEBUG else "development"),
    )
