from sqlalchemy.exc import IntegrityError
from app.extensions import db
from .models import User
from .utils import is_valid_role

def get_all_users():
    return User.query.all()

def get_user_by_id(user_id):
    return User.query.get(user_id)

def get_user_by_email(email):
    return User.query.filter_by(email=email).first()

def create_user(nom, email, password, telephone=None, role='user'):
    if not is_valid_role(role):
        role = 'user'

    new_user = User(
        nom=nom,
        email=email,
        telephone=telephone,
        role=role
    )
    new_user.set_password(password)

    try:
        db.session.add(new_user)
        db.session.commit()
        return new_user
    except IntegrityError:
        db.session.rollback()
        return None

def update_user(user_id, **kwargs):
    user = get_user_by_id(user_id)
    if not user:
        return None

    allowed_fields = {'nom', 'email', 'telephone', 'role'}
    for key, value in kwargs.items():
        if key in allowed_fields and value is not None:
            if key == 'role' and not is_valid_role(value):
                continue
            setattr(user, key, value)

    try:
        db.session.commit()
        return user
    except IntegrityError:
        db.session.rollback()
        return None

def delete_user(user_id):
    user = get_user_by_id(user_id)
    if not user:
        return False
    try:
        db.session.delete(user)
        db.session.commit()
        return True
    except Exception:
        db.session.rollback()
        return False
