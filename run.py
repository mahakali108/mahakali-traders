import os, logging, signal, sys
from dotenv import load_dotenv
from sqlalchemy import text
from app import create_app
from app.extensions import db

load_dotenv(override=False)

required_env = ['SECRET_KEY']
if os.environ.get('RENDER', '').lower() == 'true':
    required_env.append('DATABASE_URL')

missing = [env for env in required_env if not os.environ.get(env)]
if missing:
    raise RuntimeError(f"🚨 Missing required environment variables: {', '.join(missing)}")

app = create_app()

@app.shell_context_processor
def make_shell_context():
    from app.models import User, Product, Order, CartItem
    return {
        'db': db,
        'User': User,
        'Product': Product,
        'Order': Order,
        'CartItem': CartItem
    }

def test_db_connection():
    with app.app_context():
        try:
            db.session.execute(text('SELECT 1'))
            app.logger.info("✅ Database connection successful.")
            return True
        except Exception as e:
            app.logger.critical(f"🚨 Database connection failed: {e}")
            return False
        finally:
            db.session.remove()

def shutdown_handler(*args):
    app.logger.info("🛑 Gracefully shutting down application...")
    try:
        db.session.remove()
    except Exception:
        pass
    sys.exit(0)

signal.signal(signal.SIGINT, shutdown_handler)
signal.signal(signal.SIGTERM, shutdown_handler)

if not app.debug and not app.testing:
    gunicorn_logger = logging.getLogger("gunicorn.error")
    if gunicorn_logger.handlers:
        app.logger.handlers = gunicorn_logger.handlers
        app.logger.setLevel(gunicorn_logger.level)
    else:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(name)s: %(message)s"
        )

if __name__ == "__main__":
    if not test_db_connection():
        raise RuntimeError("🚨 Startup aborted due to database failure.")

    is_prod = os.environ.get('RENDER', '').lower() == 'true'

    try:
        port = int(os.environ.get("PORT", 5000))
    except ValueError:
        raise RuntimeError("🚨 Invalid PORT value.")

    if is_prod:
        app.logger.warning(
            "⚠️ Production detected. Use: gunicorn run:app"
        )
        app.run(
            host='0.0.0.0',
            port=port,
            debug=False,
            threaded=True,
            use_reloader=False
        )
    else:
        app.logger.info(f"🚀 Development server starting on port {port}")
        app.run(
            host='127.0.0.1',
            port=port,
            debug=True,
            threaded=True,
            use_reloader=False
        )
