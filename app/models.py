from datetime import datetime, timezone
from decimal import Decimal
from flask_login import UserMixin
from sqlalchemy.orm import validates, relationship
from app.extensions import db, login_manager
import re

GST_REGEX = r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$'

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(15), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=True, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    shop_name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), default='retailer', nullable=False)

    is_phone_verified = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    deleted_at = db.Column(db.DateTime(timezone=True), nullable=True)

    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    cart_items = relationship('CartItem', backref='user', lazy='selectin', cascade="all, delete-orphan")
    orders = relationship('Order', backref='user', lazy='selectin', cascade="all, delete-orphan")
    addresses = relationship('Address', backref='user', lazy='selectin', cascade="all, delete-orphan")
    audit_logs = relationship('AuditLog', backref='admin', lazy='selectin')

    __table_args__ = (
        db.CheckConstraint("role IN ('admin','wholesaler','retailer')", name='ck_user_role'),
    )

    @validates('phone')
    def validate_phone(self, key, value):
        value = value.strip().replace(" ", "")
        if not re.match(r'^\+?[1-9]\d{9,14}$', value):
            raise ValueError("Invalid phone number")
        return value

    @validates('email')
    def validate_email(self, key, value):
        if value:
            value = value.lower().strip()
            if not re.match(r'^[^@]+@[^@]+\.[^@]+$', value):
                raise ValueError("Invalid email")
        return value


class ProductCategory(db.Model):
    __tablename__ = 'product_categories'

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), unique=True, nullable=False)

    slug = db.Column(db.String(120), unique=True, nullable=False, index=True)

    products = relationship('Product', backref='category_obj', lazy='selectin')


class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)

    sku = db.Column(db.String(50), unique=True, nullable=False, index=True)

    slug = db.Column(db.String(200), unique=True, nullable=False, index=True)

    name = db.Column(db.String(150), nullable=False, index=True)

    wholesale_price = db.Column(db.Numeric(10, 2), nullable=False)

    retail_price = db.Column(db.Numeric(10, 2), nullable=False)

    stock = db.Column(db.Integer, default=0, nullable=False)

    category_id = db.Column(
        db.Integer,
        db.ForeignKey('product_categories.id', ondelete='SET NULL'),
        nullable=True
    )

    is_active = db.Column(db.Boolean, default=True, nullable=False)

    deleted_at = db.Column(db.DateTime(timezone=True), nullable=True)

    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    images = relationship('ProductImage', backref='product', lazy='selectin', cascade="all, delete-orphan")

    stock_movements = relationship('StockMovement', backref='product', lazy='selectin', cascade="all, delete-orphan")

    __table_args__ = (
        db.CheckConstraint('wholesale_price > 0', name='ck_product_wholesale_price'),
        db.CheckConstraint('retail_price > 0', name='ck_product_retail_price'),
        db.CheckConstraint('stock >= 0', name='ck_product_stock'),
    )


class ProductImage(db.Model):
    __tablename__ = 'product_images'

    id = db.Column(db.Integer, primary_key=True)

    product_id = db.Column(
        db.Integer,
        db.ForeignKey('products.id', ondelete='CASCADE'),
        nullable=False
    )

    image_filename = db.Column(db.String(255), nullable=False)

    is_primary = db.Column(db.Boolean, default=False, nullable=False)


class CartItem(db.Model):
    __tablename__ = 'cart_items'

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False
    )

    product_id = db.Column(
        db.Integer,
        db.ForeignKey('products.id', ondelete='CASCADE'),
        nullable=False
    )

    quantity = db.Column(db.Integer, default=1, nullable=False)

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    product = relationship('Product', lazy='joined')

    __table_args__ = (
        db.UniqueConstraint('user_id', 'product_id', name='uq_user_product_cart'),
        db.CheckConstraint('quantity > 0', name='ck_cart_quantity'),
    )


class Address(db.Model):
    __tablename__ = 'addresses'

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False
    )

    full_name = db.Column(db.String(120), nullable=False)

    phone = db.Column(db.String(15), nullable=False)

    address_line = db.Column(db.String(255), nullable=False)

    city = db.Column(db.String(100), nullable=False)

    state = db.Column(db.String(100), nullable=False)

    pincode = db.Column(db.String(10), nullable=False)

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    @validates('phone')
    def validate_address_phone(self, key, value):
        value = value.strip().replace(" ", "")
        if not re.match(r'^\+?[1-9]\d{9,14}$', value):
            raise ValueError("Invalid address phone number")
        return value

    @validates('pincode')
    def validate_pincode(self, key, value):
        if not re.match(r'^\d{6}$', value):
            raise ValueError("Invalid pincode")
        return value


class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False
    )

    shipping_address = db.Column(db.Text, nullable=False)

    total_amount = db.Column(db.Numeric(10, 2), nullable=False)

    status = db.Column(
        db.Enum('Pending', 'Shipped', 'Delivered', 'Cancelled', name='order_status_enum'),
        default='Pending',
        nullable=False
    )

    gst_number = db.Column(db.String(15), nullable=True)

    shipped_at = db.Column(db.DateTime(timezone=True), nullable=True)

    delivered_at = db.Column(db.DateTime(timezone=True), nullable=True)

    cancelled_at = db.Column(db.DateTime(timezone=True), nullable=True)

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    items = relationship(
        'OrderItem',
        backref='order',
        lazy='selectin',
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        db.CheckConstraint('total_amount > 0', name='ck_order_total_amount'),
    )

    @validates('gst_number')
    def validate_gst(self, key, value):
        if value:
            value = value.upper().strip()
            if not re.match(GST_REGEX, value):
                raise ValueError("Invalid GST Number")
        return value


class OrderItem(db.Model):
    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True)

    order_id = db.Column(
        db.Integer,
        db.ForeignKey('orders.id', ondelete='CASCADE'),
        nullable=False
    )

    product_id = db.Column(
        db.Integer,
        db.ForeignKey('products.id'),
        nullable=False
    )

    quantity = db.Column(db.Integer, nullable=False)

    unit_price = db.Column(db.Numeric(10, 2), nullable=False)

    subtotal = db.Column(db.Numeric(10, 2), nullable=False)

    product = relationship('Product', lazy='joined')

    __table_args__ = (
        db.CheckConstraint('quantity > 0', name='ck_order_item_quantity'),
        db.CheckConstraint('unit_price >= 0', name='ck_order_item_unit_price'),
        db.CheckConstraint('subtotal >= 0', name='ck_order_item_subtotal'),
    )

    def calculate_subtotal(self):
        self.subtotal = round(Decimal(self.quantity) * Decimal(self.unit_price), 2)


class StockMovement(db.Model):
    __tablename__ = 'stock_movements'

    id = db.Column(db.Integer, primary_key=True)

    product_id = db.Column(
        db.Integer,
        db.ForeignKey('products.id', ondelete='CASCADE'),
        nullable=False
    )

    old_stock = db.Column(db.Integer, nullable=False)

    new_stock = db.Column(db.Integer, nullable=False)

    reason = db.Column(db.String(255))

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        db.CheckConstraint('old_stock >= 0', name='ck_old_stock_positive'),
        db.CheckConstraint('new_stock >= 0', name='ck_new_stock_positive'),
    )


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)

    admin_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='SET NULL')
    )

    action = db.Column(db.String(255), nullable=False, index=True)

    ip_address = db.Column(db.String(45), nullable=True)

    user_agent = db.Column(db.Text, nullable=True)

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )


@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(User, int(user_id))
    except (TypeError, ValueError):
        return None
      
