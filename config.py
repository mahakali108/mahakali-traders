import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))

# Instance folder for SQLite & secure local storage
instance_path = os.path.join(basedir, "instance")
os.makedirs(instance_path, exist_ok=True)

# Upload folder auto-create
upload_path = os.path.join(basedir, "app/static/uploads")
os.makedirs(upload_path, exist_ok=True)


class Config:
    # =========================================================
    # 1. SECRET KEY CONFIGURATION
    # =========================================================
    SECRET_KEY = os.environ.get('SECRET_KEY')

    # Strict production validation for Render
    if os.environ.get('RENDER', '').lower() == 'true' and not SECRET_KEY:
        raise ValueError(
            "🚨 CRITICAL: SECRET_KEY is missing in Render production!"
        )

    # Safe local development fallback
    elif not SECRET_KEY:
        SECRET_KEY = os.urandom(32).hex()

    # =========================================================
    # 2. DATABASE CONFIGURATION
    # =========================================================
    database_url = os.environ.get('DATABASE_URL')

    # Prevent SQLite usage on Render production
    if os.environ.get('RENDER', '').lower() == 'true' and not database_url:
        raise ValueError(
            "🚨 CRITICAL: DATABASE_URL missing. SQLite is not allowed on Render Production!"
        )

    # Fix old postgres:// URLs
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace(
            "postgres://",
            "postgresql://",
            1
        )

    # PostgreSQL or local SQLite fallback
    SQLALCHEMY_DATABASE_URI = (
        database_url or
        f"sqlite:///{os.path.join(instance_path, 'mahakali_pro.db')}"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = False

    # PostgreSQL stability settings
    if database_url and "postgresql" in database_url:
        SQLALCHEMY_ENGINE_OPTIONS = {
            "pool_pre_ping": True,
            "pool_recycle": 300,
            "connect_args": {
                "sslmode": "require"
            }
        }

    # =========================================================
    # 3. SESSION & COOKIE SECURITY
    # =========================================================
    SESSION_COOKIE_NAME = "mahakali_session"
    REMEMBER_COOKIE_NAME = "mahakali_remember"

    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True

    SESSION_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_SAMESITE = "Lax"

    # Explicit dev defaults
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False

    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    REMEMBER_COOKIE_DURATION = timedelta(days=7)

    SESSION_REFRESH_EACH_REQUEST = True

    # =========================================================
    # 4. CSRF SECURITY
    # =========================================================
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600

    # =========================================================
    # 5. FILE UPLOAD SETTINGS
    # =========================================================
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024
    UPLOAD_FOLDER = upload_path

    # =========================================================
    # 6. FLASK OPTIMIZATION
    # =========================================================
    JSON_SORT_KEYS = False

    # Auto reload only in development
    TEMPLATES_AUTO_RELOAD = (
        os.environ.get("FLASK_ENV") == "development"
    )

    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

    # =========================================================
    # 7. STRICT PRODUCTION SETTINGS
    # =========================================================
    if os.environ.get('RENDER', '').lower() == 'true':
        SESSION_COOKIE_SECURE = True
        REMEMBER_COOKIE_SECURE = True
        PREFERRED_URL_SCHEME = "https"
