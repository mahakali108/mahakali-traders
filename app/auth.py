import time
import logging
from urllib.parse import urlparse
from sqlalchemy.exc import IntegrityError
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, session, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, current_user, login_required
from flask_limiter.util import get_remote_address
from app.extensions import db, limiter
from app.models import User, AuditLog
from app.forms import RegistrationForm, LoginForm

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

logger = logging.getLogger(__name__)

FAILED_LOGINS = {}

DUMMY_HASH = generate_password_hash("invalid_password_secure_dummy")

def is_safe_url(target):
    if not target:
        return False
    ref_url = urlparse(request.host_url)
    test_url = urlparse(target)
    return (
        test_url.scheme in ('http', 'https', '') and
        ref_url.netloc == test_url.netloc
    )

def log_event(action):
    try:
        log = AuditLog(
            action=action,
            ip_address=get_remote_address(),
            user_agent=request.headers.get('User-Agent', '')[:255],
            admin_id=current_user.id if current_user.is_authenticated else None
        )
        db.session.add(log)
        db.session.commit()
    except Exception:
        db.session.rollback()

@auth_bp.after_request
def add_no_cache_headers(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@auth_bp.route('/register', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = RegistrationForm()

    if form.validate_on_submit():
        try:
            existing_user = User.query.filter(
                (User.phone == form.phone.data) |
                (User.email == form.email.data.lower())
            ).first()

            if existing_user:
                flash('यह अकाउंट पहले से मौजूद है।', 'warning')
                return redirect(url_for('auth.login'))

            hashed_password = generate_password_hash(
                form.password.data,
                method='pbkdf2:sha256:600000'
            )

            new_user = User(
                phone=form.phone.data,
                email=form.email.data.lower(),
                shop_name=form.shop_name.data,
                password_hash=hashed_password,
                role='retailer',
                is_active=True
            )

            db.session.add(new_user)
            db.session.commit()

            log_event(f"New user registered: {new_user.phone}")

            flash('रजिस्ट्रेशन सफल रहा। कृपया लॉगिन करें।', 'success')
            return redirect(url_for('auth.login'))

        except IntegrityError:
            db.session.rollback()
            flash('यह मोबाइल नंबर या ईमेल पहले से उपयोग में है।', 'danger')

        except Exception as e:
            db.session.rollback()
            logger.exception("Registration Error")
            flash('तकनीकी समस्या आई। कृपया बाद में प्रयास करें।', 'danger')

    response = make_response(render_template('auth/register.html', form=form))
    return response

@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()

    ip = get_remote_address()

    if FAILED_LOGINS.get(ip, 0) >= 10:
        abort(429)

    if form.validate_on_submit():
        user = User.query.filter_by(phone=form.phone.data).first()

        password_valid = False

        if user:
            password_valid = check_password_hash(user.password_hash, form.password.data)
        else:
            check_password_hash(DUMMY_HASH, form.password.data)

        if (
            user and
            password_valid and
            user.is_active and
            not user.deleted_at
        ):
            session.clear()

            login_user(
                user,
                remember=False,
                fresh=True
            )

            session.permanent = True

            FAILED_LOGINS[ip] = 0

            log_event(f"Successful login: {user.phone}")

            next_page = request.args.get('next')

            if not next_page or not is_safe_url(next_page):
                next_page = url_for('main.index')

            flash('लॉगिन सफल रहा।', 'success')
            return redirect(next_page)

        FAILED_LOGINS[ip] = FAILED_LOGINS.get(ip, 0) + 1

        log_event(f"Failed login attempt for phone: {form.phone.data}")

        time.sleep(1)

        flash('गलत मोबाइल नंबर या पासवर्ड।', 'danger')

    response = make_response(render_template('auth/login.html', form=form))
    return response

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    try:
        log_event(f"User logout: {current_user.phone}")
    except Exception:
        pass

    logout_user()
    session.clear()

    flash('आप सफलतापूर्वक लॉग आउट हो गए हैं।', 'info')

    return redirect(url_for('auth.login'))
