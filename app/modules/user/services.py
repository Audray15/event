from sqlalchemy.exc import IntegrityError
from app.extensions import db
from .models import User

def get_all_users():
    return User.query.all()

def get_user_by_id(user_id):
    return User.query.get(user_id)

def get_user_by_email(email):
    return User.query.filter_by(email=email).first()

def create_user(nom, email, password, telephone=None, role='user'):
    # Validation du rôle
    valid_roles = ['visitor', 'user', 'organizer', 'admin', 'super_admin']
    if role not in valid_roles:
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

def change_password_service(user_id, old_password, new_password):
    user = get_user_by_id(user_id)
    if not user:
        return None, "Utilisateur non trouvé."

    if not user.check_password(old_password):
        return None, "L'ancien mot de passe est incorrect."

    if old_password == new_password:
        return None, "Le nouveau mot de passe doit être différent de l'ancien."

    user.set_password(new_password)
    try:
        db.session.commit()
        return user, None
    except Exception as e:
        db.session.rollback()
        return None, "Erreur lors de la mise à jour du mot de passe."