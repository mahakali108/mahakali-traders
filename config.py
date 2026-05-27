import os
from datetime import timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Config:

    # =========================================================
    # CORE APP
    # =========================================================
    APP_NAME = "Mahakali Traders"
    APP_VERSION = "2.0.0"
    API_VERSION = "v1"

    ENV = os.environ.get("FLASK_ENV", "production").lower()
    DEBUG = ENV == "development"
    TESTING = False

    # =========================================================
    # SECURITY
    # =========================================================
    SECRET_KEY = os.environ.get("SECRET_KEY")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", SECRET_KEY)
    SECURITY_PASSWORD_SALT = os.environ.get("SECURITY_PASSWORD_SALT")

    if not SECRET_KEY:
        raise RuntimeError("SECRET_KEY missing")

    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600

    SESSION_COOKIE_NAME = "mahakali_session"
    REMEMBER_COOKIE_NAME = "mahakali_remember"

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_HTTPONLY = True

    IS_PRODUCTION = ENV == "production"

    SESSION_COOKIE_SECURE = IS_PRODUCTION
    REMEMBER_COOKIE_SECURE = IS_PRODUCTION

    REMEMBER_COOKIE_DURATION = timedelta(days=14)
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)

    SESSION_REFRESH_EACH_REQUEST = True

    # =========================================================
    # DATABASE
    # =========================================================
    DATABASE_URL = os.environ.get("DATABASE_URL")

    if ENV == "production" and not DATABASE_URL:
        raise RuntimeError("DATABASE_URL missing")

    SQLALCHEMY_DATABASE_URI = DATABASE_URL or "sqlite:///mahakali.db"

    if SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace(
            "postgres://",
            "postgresql://",
            1
        )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "pool_size": 10,
        "max_overflow": 20,
        "pool_timeout": 30,
        "pool_reset_on_return": "rollback",
        "connect_args": {
            "connect_timeout": 10
        }
    }

    DB_QUERY_TIMEOUT = 30

    # =========================================================
    # REDIS / CACHE
    # =========================================================
    REDIS_URL = os.environ.get("REDIS_URL")

    CACHE_TYPE = "RedisCache" if REDIS_URL else "SimpleCache"

    CACHE_DEFAULT_TIMEOUT = 300
    CACHE_KEY_PREFIX = "mahakali_cache_v2"

    if REDIS_URL:
        CACHE_REDIS_URL = REDIS_URL

    # =========================================================
    # RATE LIMITING
    # =========================================================
    RATELIMIT_ENABLED = True

    RATELIMIT_STORAGE_URI = REDIS_URL or "memory://"

    RATELIMIT_HEADERS_ENABLED = True

    RATELIMIT_DEFAULT = "300/day;100/hour"

    LOGIN_RATE_LIMIT = "5/minute"
    OTP_RATE_LIMIT = "3/minute"
    API_RATE_LIMIT = "100/minute"

    ADMIN_RATE_LIMIT = "1000/hour"

    MAX_LOGIN_ATTEMPTS = 5
    ACCOUNT_LOCK_TIME = 900

    # =========================================================
    # FILE UPLOADS
    # =========================================================
    UPLOAD_FOLDER = os.environ.get(
        "UPLOAD_FOLDER",
        str(BASE_DIR / "app/static/uploads")
    )

    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

    ALLOWED_IMAGE_EXTENSIONS = {
        "png",
        "jpg",
        "jpeg",
        "webp"
    }

    ALLOWED_IMAGE_MIMES = {
        "image/png",
        "image/jpeg",
        "image/webp"
    }

    IMAGE_QUALITY = 85
    IMAGE_MAX_WIDTH = 1920
    IMAGE_MAX_HEIGHT = 1920
    THUMBNAIL_SIZE = (300, 300)

    ENABLE_IMAGE_VIRUS_SCAN = False

    # =========================================================
    # STORAGE
    # =========================================================
    STORAGE_PROVIDER = os.environ.get("STORAGE_PROVIDER", "local")

    AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
    AWS_BUCKET_NAME = os.environ.get("AWS_BUCKET_NAME")
    AWS_REGION = os.environ.get("AWS_REGION")

    CLOUDINARY_URL = os.environ.get("CLOUDINARY_URL")

    CDN_URL = os.environ.get("CDN_URL", "")

    # =========================================================
    # EMAIL
    # =========================================================
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")

    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))

    MAIL_USE_TLS = os.environ.get(
        "MAIL_USE_TLS",
        "true"
    ).lower() in ["true", "1", "on"]

    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")

    MAIL_DEFAULT_SENDER = os.environ.get(
        "MAIL_DEFAULT_SENDER",
        "noreply@mahakalitraders.com"
    )

    MAIL_TIMEOUT = 10
    MAIL_MAX_EMAILS = 100

    # =========================================================
    # OTP
    # =========================================================
    OTP_EXPIRY = 300
    OTP_LENGTH = 6
    OTP_MAX_ATTEMPTS = 5

    # =========================================================
    # JWT
    # =========================================================
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    # =========================================================
    # PASSWORD POLICY
    # =========================================================
    PASSWORD_MIN_LENGTH = 8
    PASSWORD_MAX_LENGTH = 64

    PASSWORD_REQUIRE_UPPERCASE = True
    PASSWORD_REQUIRE_LOWERCASE = True
    PASSWORD_REQUIRE_NUMBER = True
    PASSWORD_REQUIRE_SPECIAL = True

    # =========================================================
    # CORS
    # =========================================================
    CORS_SUPPORTS_CREDENTIALS = True

    CORS_ORIGINS = os.environ.get(
        "CORS_ORIGINS",
        "*"
    ).split(",")

    # =========================================================
    # SECURITY HEADERS
    # =========================================================
    SECURITY_HEADERS = {
        "X-Frame-Options": "SAMEORIGIN",
        "X-Content-Type-Options": "nosniff",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "camera=(), microphone=(), geolocation=()"
    }

    CONTENT_SECURITY_POLICY = {
        "default-src": "'self'",
        "img-src": "'self' data: https:",
        "script-src": "'self' 'unsafe-inline' https://cdn.jsdelivr.net",
        "style-src": "'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com",
        "font-src": "'self' https://fonts.gstatic.com https://cdn.jsdelivr.net"
    }

    # =========================================================
    # PAYMENT GATEWAY
    # =========================================================
    RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID")
    RAZORPAY_SECRET = os.environ.get("RAZORPAY_SECRET")
    PAYMENT_WEBHOOK_SECRET = os.environ.get("PAYMENT_WEBHOOK_SECRET")

    # =========================================================
    # AI
    # =========================================================
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

    # =========================================================
    # ANALYTICS
    # =========================================================
    GOOGLE_ANALYTICS_ID = os.environ.get("GOOGLE_ANALYTICS_ID")

    # =========================================================
    # SEARCH
    # =========================================================
    ELASTICSEARCH_URL = os.environ.get("ELASTICSEARCH_URL")
    MEILISEARCH_URL = os.environ.get("MEILISEARCH_URL")

    # =========================================================
    # WEBSOCKET
    # =========================================================
    SOCKETIO_MESSAGE_QUEUE = REDIS_URL

    # =========================================================
    # CELERY
    # =========================================================
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL

    CELERY_TASK_ACKS_LATE = True
    CELERY_TASK_REJECT_ON_WORKER_LOST = True

    CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

    # =========================================================
    # BACKUP
    # =========================================================
    BACKUP_STORAGE_PATH = str(BASE_DIR / "backups")

    BACKUP_RETENTION_DAYS = 7

    # =========================================================
    # TEMP CLEANUP
    # =========================================================
    TEMP_FILE_EXPIRY = 3600

    # =========================================================
    # ADMIN SECURITY
    # =========================================================
    ADMIN_ALLOWED_IPS = os.environ.get(
        "ADMIN_ALLOWED_IPS",
        ""
    ).split(",")

    MAINTENANCE_MODE = False
    MAINTENANCE_BYPASS_TOKEN = os.environ.get(
        "MAINTENANCE_BYPASS_TOKEN"
    )

    # =========================================================
    # AUDIT LOGS
    # =========================================================
    AUDIT_LOG_RETENTION_DAYS = 90

    # =========================================================
    # GEOLOCATION
    # =========================================================
    GEOIP_DB_PATH = str(BASE_DIR / "geoip/GeoLite2.mmdb")

    # =========================================================
    # MONITORING
    # =========================================================
    SENTRY_DSN = os.environ.get("SENTRY_DSN")

    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

    # =========================================================
    # FEATURE FLAGS
    # =========================================================
    ENABLE_ANALYTICS = True
    ENABLE_API = True
    ENABLE_AI = True
    ENABLE_OTP = True
    ENABLE_REGISTRATION = True
    ENABLE_EMAIL_NOTIFICATIONS = True
    ENABLE_ORDER_TRACKING = True
    ENABLE_REALTIME_NOTIFICATIONS = True

    # =========================================================
    # CLOUD DEPLOYMENT
    # =========================================================
    WEB_CONCURRENCY = int(os.environ.get("WEB_CONCURRENCY", 2))

    PREFERRED_URL_SCHEME = "https" if IS_PRODUCTION else "http"

    # =========================================================
    # HEALTH CHECK
    # =========================================================
    HEALTHCHECK_TIMEOUT = 5

    # =========================================================
    # JSON
    # =========================================================
    JSON_SORT_KEYS = False
    JSONIFY_PRETTYPRINT_REGULAR = False

    # =========================================================
    # COMPRESSION
    # =========================================================
    COMPRESS_LEVEL = 6

    COMPRESS_MIMETYPES = [
        "text/html",
        "text/css",
        "application/json",
        "application/javascript"
    ]

    # =========================================================
    # STATIC CACHE
    # =========================================================
    SEND_FILE_MAX_AGE_DEFAULT = 31536000

    # =========================================================
    # REQUIRED ENV VALIDATION
    # =========================================================
    REQUIRED_ENV_VARS = [
        "SECRET_KEY"
    ]

    if IS_PRODUCTION:
        REQUIRED_ENV_VARS.append("DATABASE_URL")

    missing = [
        var for var in REQUIRED_ENV_VARS
        if not os.environ.get(var)
    ]

    if missing:
        raise RuntimeError(
            f"Missing environment variables: {', '.join(missing)}"
        )


class DevelopmentConfig(Config):
    ENV = "development"
    DEBUG = True
    SESSION_COOKIE_SECURE = False


class TestingConfig(Config):
    ENV = "testing"
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


class ProductionConfig(Config):
    ENV = "production"
    DEBUG = False
    TESTING = False
