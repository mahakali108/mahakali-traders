# app/__init__.py Enterprise Hardened Version

import os
import uuid
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, request, jsonify, g
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.exceptions import RequestEntityTooLarge
from flask_talisman import Talisman
from flask_compress import Compress
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from config import Config
from app.extensions import db, login_manager, csrf, migrate

compress = Compress()
limiter = Limiter(key_func=get_remote_address)

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # 1. Environment Validation
    required_envs = ['SECRET_KEY']
    if os.environ.get('RENDER', '').lower() == 'true':
        required_envs.append('DATABASE_URL')

    missing = [env for env in required_envs if not os.environ.get(env)]
    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")

    # 2. Upload Folder Creation
    upload_folder = app.config.get(
        'UPLOAD_FOLDER',
        os.path.join(app.root_path, 'static/uploads')
    )

    try:
        os.makedirs(upload_folder, exist_ok=True)
    except OSError as e:
        raise RuntimeError(f"Upload folder creation failed: {e}")

    # 3. ProxyFix for Render
    if os.environ.get('RENDER', '').lower() == 'true':
        app.wsgi_app = ProxyFix(
            app.wsgi_app,
            x_for=1,
            x_proto=1,
            x_host=1
        )

    # 4. Initialize Extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)
    compress.init_app(app)
    limiter.init_app(app)

    # 5. Login Security
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'error'
    login_manager.login_message = "कृपया लॉगिन करें।"
    login_manager.session_protection = "strong"

    # 6. Compression Optimization
    app.config['COMPRESS_MIMETYPES'] = [
        'text/html',
        'text/css',
        'application/json',
        'application/javascript'
    ]
    app.config['COMPRESS_LEVEL'] = 6
    app.config['COMPRESS_MIN_SIZE'] = 500

    # 7. Security Headers
    is_prod = os.environ.get('RENDER', '').lower() == 'true'

    Talisman(
        app,
        force_https=is_prod,
        strict_transport_security=is_prod,
        session_cookie_secure=is_prod,
        content_security_policy={
            'default-src': "'self'",
            'script-src': ["'self'"],
            'style-src': ["'self'", "'unsafe-inline'"],
            'img-src': ["'self'", "data:", "https:"],
            'font-src': ["'self'", "https:", "data:"]
        }
    )

    # 8. Request Tracking
    @app.before_request
    def attach_request_id():
        g.request_id = str(uuid.uuid4())

    # 9. Structured Logging
    if not app.debug and not app.testing:
        gunicorn_logger = logging.getLogger('gunicorn.error')

        if gunicorn_logger.handlers:
            app.logger.handlers = gunicorn_logger.handlers
            app.logger.setLevel(gunicorn_logger.level)
        else:
            formatter = logging.Formatter(
                '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
            )

            file_handler = RotatingFileHandler(
                'logs/app.log',
                maxBytes=10 * 1024 * 1024,
                backupCount=5
            )

            file_handler.setFormatter(formatter)
            file_handler.setLevel(logging.INFO)

            app.logger.addHandler(file_handler)
            app.logger.setLevel(logging.INFO)

        app.logger.info('Mahakali Traders Production Engine Started')

    # 10. Health Check
    @app.route('/health')
    @limiter.limit("30 per minute")
    def health():
        try:
            db.session.execute(text('SELECT 1'))
            return jsonify({
                "status": "ok",
                "service": "mahakali-traders"
            }), 200

        except SQLAlchemyError as e:
            db.session.rollback()

            app.logger.error(
                f"Health Check Failed | RequestID={g.request_id} | Error={str(e)}"
            )

            return jsonify({
                "status": "db_error"
            }), 500

    # 11. Global Error Handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "error": "Page not found"
        }), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()

        app.logger.error(
            f"Internal Server Error | RequestID={g.request_id} | Error={str(error)}"
        )

        return jsonify({
            "error": "Internal server error"
        }), 500

    @app.errorhandler(RequestEntityTooLarge)
    def handle_large_file(error):
        return jsonify({
            "error": "File size exceeds allowed limit"
        }), 413

    # 12. Request Cleanup
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        if exception:
            db.session.rollback()
        db.session.remove()

    # 13. Import Models
    with app.app_context():
        from app import models

    # 14. Blueprint Registration
    from app.routes.auth import auth_bp
    from app.routes.shop import shop_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(shop_bp)
    app.register_blueprint(admin_bp)

    return app
