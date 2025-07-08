from app.extensions import db
from app.modules.user.models import User
from sqlalchemy.exc import IntegrityError
from flask_jwt_extended import create_access_token, create_refresh_token
from datetime import timedelta

def create_user_service(data):
    try:
        nom = data.get("nom")
        email = data.get("email")
        password = data.get("password")
        telephone = data.get("telephone")
        role = data.get("role", "user")

        if not all([nom, email, password]):
            return {"message": "Tous les champs obligatoires ne sont pas fournis.", "status": 400}

        if User.query.filter_by(email=email).first():
            return {"message": "Cet email est déjà utilisé.", "status": 409}

        user = User(nom=nom, email=email, telephone=telephone, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        return {
            "message": "Utilisateur créé avec succès.",
            "user": {
                "id": user.id,
                "nom": user.nom,
                "email": user.email,
                "role": user.role,
                "telephone": user.telephone,
                "created_at": user.created_at.isoformat() if user.created_at else None
            },
            "status": 201
        }
    except IntegrityError:
        db.session.rollback()
        return {"message": "Erreur d'intégrité. L'utilisateur n'a pas pu être créé.", "status": 500}
    except Exception as e:
        db.session.rollback()
        return {"message": str(e), "status": 500}


def authenticate_user_service(email, password):
    user = User.query.filter_by(email=email).first()

    if not user or not user.check_password(password):
        return None, "Email ou mot de passe incorrect."

    if not user.is_active:
        return None, "Ce compte est désactivé."

    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={"role": user.role},
        expires_delta=timedelta(hours=1)
    )

    refresh_token = create_refresh_token(
        identity=str(user.id),
        expires_delta=timedelta(days=7)
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": {
            "id": user.id,
            "nom": user.nom,
            "email": user.email,
            "role": user.role,
            "telephone": user.telephone,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }
    }, None
