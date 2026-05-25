import re
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo, Regexp, Email, ValidationError
from app.models import User

def normalize_phone(phone):
    if not phone:
        return None
    phone = re.sub(r'[\s\-()]', '', phone.strip())
    if phone.startswith('+91'):
        phone = phone[3:]
    elif phone.startswith('0') and len(phone) == 11:
        phone = phone[1:]
    return phone

def normalize_text(text):
    return text.strip() if text else None

class RegistrationForm(FlaskForm):
    phone = StringField(
        'Mobile Number',
        filters=[normalize_phone],
        validators=[
            DataRequired(message="मोबाइल नंबर ज़रूरी है।"),
            Regexp(r'^[6-9]\d{9}$', message="कृपया सही 10-अंकों का भारतीय मोबाइल नंबर डालें।")
        ]
    )

    email = StringField(
        'Email Address',
        filters=[lambda x: x.lower().strip() if x else None],
        validators=[
            DataRequired(message="ईमेल ज़रूरी है।"),
            Email(message="कृपया सही ईमेल डालें।"),
            Length(max=255, message="ईमेल बहुत लंबा है।")
        ]
    )

    shop_name = StringField(
        'Shop Name',
        filters=[normalize_text],
        validators=[
            DataRequired(message="दुकान का नाम ज़रूरी है।"),
            Length(min=2, max=120, message="दुकान का नाम 2 से 120 अक्षरों के बीच होना चाहिए।")
        ]
    )

    password = PasswordField(
        'Password',
        validators=[
            DataRequired(message="पासवर्ड ज़रूरी है।"),
            Length(min=8, max=128, message="पासवर्ड 8 से 128 अक्षरों के बीच होना चाहिए।"),
            Regexp(
                r'^(?=.*[A-Za-z])(?=.*\d).+$',
                message="पासवर्ड में कम से कम एक अक्षर और एक नंबर होना चाहिए।"
            )
        ]
    )

    confirm_password = PasswordField(
        'Confirm Password',
        validators=[
            DataRequired(message="पासवर्ड कन्फर्म करें।"),
            EqualTo('password', message="पासवर्ड मैच नहीं हो रहे हैं।")
        ]
    )

    submit = SubmitField('Sign Up')

    def validate_phone(self, phone):
        existing_user = User.query.filter_by(phone=phone.data).first()
        if existing_user:
            raise ValidationError('यह मोबाइल नंबर पहले से रजिस्टर है।')

    def validate_email(self, email):
        existing_user = User.query.filter_by(email=email.data.lower()).first()
        if existing_user:
            raise ValidationError('यह ईमेल पहले से रजिस्टर है।')

class LoginForm(FlaskForm):
    phone = StringField(
        'Mobile Number',
        filters=[normalize_phone],
        validators=[
            DataRequired(message="मोबाइल नंबर ज़रूरी है।"),
            Regexp(r'^[6-9]\d{9}$', message="कृपया सही मोबाइल नंबर डालें।")
        ]
    )

    password = PasswordField(
        'Password',
        validators=[
            DataRequired(message="पासवर्ड ज़रूरी है।"),
            Length(min=8, max=128, message="अमान्य पासवर्ड।")
        ]
    )

    submit = SubmitField('Login')
  
