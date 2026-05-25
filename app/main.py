import logging
from flask import (
    Blueprint,
    render_template,
    request,
    abort,
    flash,
    redirect,
    url_for,
    jsonify,
    current_app
)
from flask_login import (
    login_required,
    current_user,
    fresh_login_required
)
from flask_limiter.util import get_remote_address
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from app.extensions import db, limiter
from app.models import (
    Product,
    Order,
    CartItem,
    AuditLog,
    User
)

logger = logging.getLogger(__name__)

main_bp = Blueprint(
    'main',
    __name__,
    template_folder='templates',
    static_folder='static'
)

# -----------------------------
# Utility Functions
# -----------------------------

def log_event(action):
    try:
        log = AuditLog(
            admin_id=current_user.id if current_user.is_authenticated else None,
            action=action,
            ip_address=get_remote_address(),
            user_agent=request.headers.get('User-Agent', '')[:255]
        )
        db.session.add(log)
        db.session.commit()
    except Exception:
        db.session.rollback()

def ensure_active_user():
    if (
        current_user.is_authenticated and
        (
            not getattr(current_user, "is_active", True) or
            getattr(current_user, "deleted_at", None)
        )
    ):
        flash("आपका अकाउंट निष्क्रिय कर दिया गया है।", "danger")
        return False
    return True

# -----------------------------
# Request Hooks
# -----------------------------

@main_bp.before_request
def before_request_checks():

    # Maintenance mode support
    if current_app.config.get("MAINTENANCE_MODE", False):
        return render_template(
            "errors/maintenance.html"
        ), 503

    # Authenticated user validation
    if current_user.is_authenticated:
        if not ensure_active_user():
            abort(403)

# -----------------------------
# Error Handlers
# -----------------------------

@main_bp.app_errorhandler(404)
def not_found_error(error):
    return render_template(
        "errors/404.html"
    ), 404

@main_bp.app_errorhandler(403)
def forbidden_error(error):
    return render_template(
        "errors/403.html"
    ), 403

@main_bp.app_errorhandler(429)
def rate_limit_error(error):
    return render_template(
        "errors/429.html"
    ), 429

@main_bp.app_errorhandler(500)
def internal_error(error):
    db.session.rollback()
    logger.exception("Internal Server Error")
    return render_template(
        "errors/500.html"
    ), 500

# -----------------------------
# Home Page
# -----------------------------

@main_bp.route("/")
@limiter.limit("60 per minute")
def index():

    try:
        featured_products = (
            Product.query
            .filter_by(is_active=True)
            .order_by(Product.created_at.desc())
            .limit(8)
            .all()
        )

        response = render_template(
            "main/index.html",
            products=featured_products,
            page_title="महाकाली ट्रेडर्स",
            meta_description="Secure B2B Wholesale Platform",
            current_year=2026
        )

        return response

    except SQLAlchemyError:
        logger.exception("Homepage DB Error")
        abort(500)

# -----------------------------
# Dashboard
# -----------------------------

@main_bp.route("/dashboard")
@login_required
@fresh_login_required
@limiter.limit("30 per minute")
def dashboard():

    try:

        if not ensure_active_user():
            abort(403)

        # Role-based redirect
        if current_user.role == "admin":
            dashboard_template = "dashboard/admin.html"

        elif current_user.role == "wholesaler":
            dashboard_template = "dashboard/wholesaler.html"

        else:
            dashboard_template = "dashboard/retailer.html"

        # Dashboard Stats
        total_orders = (
            Order.query
            .filter_by(user_id=current_user.id)
            .count()
        )

        cart_count = (
            CartItem.query
            .filter_by(user_id=current_user.id)
            .count()
        )

        recent_orders = (
            Order.query
            .filter_by(user_id=current_user.id)
            .order_by(Order.created_at.desc())
            .limit(5)
            .all()
        )

        # Health ping
        db.session.execute(text("SELECT 1"))

        log_event(
            f"Dashboard Accessed by User ID {current_user.id}"
        )

        return render_template(
            dashboard_template,
            total_orders=total_orders,
            cart_count=cart_count,
            recent_orders=recent_orders,
            current_year=2026,
            page_title="Dashboard"
        )

    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Dashboard DB Error")
        abort(500)

# -----------------------------
# Profile
# -----------------------------

@main_bp.route("/profile")
@login_required
@limiter.limit("20 per minute")
def profile():

    try:
        return render_template(
            "main/profile.html",
            user=current_user,
            page_title="Profile"
        )

    except Exception:
        logger.exception("Profile Error")
        abort(500)

# -----------------------------
# Notifications API
# -----------------------------

@main_bp.route("/api/notifications")
@login_required
@limiter.limit("30 per minute")
def notifications_api():

    try:
        data = {
            "success": True,
            "notifications": [],
            "user": current_user.shop_name
        }

        return jsonify(data), 200

    except Exception:
        logger.exception("Notification API Error")

        return jsonify({
            "success": False,
            "message": "Server Error"
        }), 500

# -----------------------------
# Health Check
# -----------------------------

@main_bp.route("/health")
@limiter.exempt
def health():

    try:
        db.session.execute(text("SELECT 1"))

        return jsonify({
            "status": "ok",
            "service": "Mahakali Traders",
            "database": "connected"
        }), 200

    except Exception:
        logger.exception("Health Check Failed")

        return jsonify({
            "status": "error"
        }), 500

# -----------------------------
# Robots.txt
# -----------------------------

@main_bp.route("/robots.txt")
def robots():

    return (
        "User-agent: *\nAllow: /\n",
        200,
        {"Content-Type": "text/plain"}
    )

# -----------------------------
# Sitemap
# -----------------------------

@main_bp.route("/sitemap.xml")
def sitemap():

    xml = render_template(
        "seo/sitemap.xml"
    )

    return current_app.response_class(
        xml,
        mimetype="application/xml"
    )

# -----------------------------
# Maintenance Page
# -----------------------------

@main_bp.route("/maintenance")
def maintenance():
    return render_template(
        "errors/maintenance.html"
    ), 503

# -----------------------------
# Security Headers
# -----------------------------

@main_bp.after_request
def add_security_headers(response):

    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    response.headers["Cache-Control"] = "no-store"

    return response
