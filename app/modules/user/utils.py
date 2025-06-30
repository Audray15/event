import re
from flask import current_app
from flask_jwt_extended import get_jwt
from .models import User

def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email) is not None

def is_valid_role(role):
    valid_roles = ['visitor', 'user', 'organizer', 'admin', 'super_admin']
    return role in valid_roles

def email_exists(email):
    return User.query.filter_by(email=email).first() is not None

def log_info(message):
    current_app.logger.info(f"[INFO] {message}")

def log_error(message):
    current_app.logger.error(f"[ERROR] {message}")

def is_admin():
    claims = get_jwt()
    return claims.get('role') in ['admin', 'super_admin']
