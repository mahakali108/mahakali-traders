from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate

# Advanced Naming Convention (Stable for Alembic & Flask-Migrate)
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

db_metadata = MetaData(naming_convention=convention)

# Initialize Extensions
db = SQLAlchemy(metadata=db_metadata)

login_manager = LoginManager()
login_manager.session_protection = "strong"
login_manager.login_view = "auth.login"
login_manager.login_message_category = "error"
login_manager.login_message = "कृपया पहले लॉगिन करें।"

csrf = CSRFProtect()

migrate = Migrate()
