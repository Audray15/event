from flask import request, jsonify, current_app
import smtplib
from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity,
    get_jwt,
    create_access_token,
    create_refresh_token
)
from datetime import timedelta, datetime
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Message
from app.extensions import db, mail
from app.modules.user.models import User
from . import auth_bp
from .services import (
    create_user_service,
    authenticate_user_service
)
from .utils import revoke_token

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    response = create_user_service(data)
    return jsonify(response), response.get("status", 400)

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user_data, error = authenticate_user_service(data.get("email"), data.get("password"))
    
    if error:
        return jsonify({"message": error}), 401
    
    return jsonify({
        "message": "Connexion réussie",
        "access_token": user_data["access_token"],
        "refresh_token": user_data["refresh_token"],
        "user": user_data["user"]
    }), 200

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh_token():
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity)
    return jsonify({"access_token": access_token}), 200

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    jti = get_jwt()["jti"]
    revoke_token(jti)
    return jsonify({"message": "Déconnexion réussie"}), 200

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    try:
        email = request.json.get('email')
        if not email:
            return jsonify({"error": "Email requis"}), 400

        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"message": "Si l'email existe, un code a été envoyé"}), 200

        # Générer et envoyer le code
        reset_code = user.generate_reset_code()
        db.session.commit()

        # Envoi du code par email
        with smtplib.SMTP(current_app.config['MAIL_SERVER'], 
                         current_app.config['MAIL_PORT']) as server:
            server.starttls()
            server.login(current_app.config['MAIL_USERNAME'],
                        current_app.config['MAIL_PASSWORD'])
            
            message = f"""Subject: Code de réinitialisation
From: {current_app.config['MAIL_DEFAULT_SENDER']}
To: {email}

Votre code de réinitialisation est : {reset_code}
Valable 10 minutes."""
            
            server.sendmail(
                current_app.config['MAIL_DEFAULT_SENDER'],
                [email],
                message.encode('utf-8')
            )

        return jsonify({"message": "Code envoyé par email"}), 200

    except smtplib.SMTPAuthenticationError:
        return jsonify({
            "error": "Erreur d'authentification SMTP",
            "solution": "Vérifiez le mot de passe d'application dans .env"
        }), 503
    except Exception as e:
        current_app.logger.error(f"Erreur: {str(e)}")
        return jsonify({"error": str(e)}), 500

@auth_bp.route('/verify-reset-code', methods=['POST'])
def verify_reset_code():
    data = request.get_json()
    email = data.get('email')
    code = data.get('code')
    
    if not email or not code:
        return jsonify({"error": "Email et code requis"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "Utilisateur non trouvé"}), 404
    
    if user.is_reset_code_valid(code):
        return jsonify({
            "message": "Code valide",
            "email": email
        }), 200
    
    return jsonify({"error": "Code invalide ou expiré"}), 400

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    data = request.get_json()
    email = data.get('email')
    new_password = data.get('password')
    
    if not email or not new_password:
        return jsonify({"error": "Email et mot de passe requis"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "Utilisateur non trouvé"}), 404

    try:
        user.set_password(new_password)
        user.reset_code = None  # Invalider le code après utilisation
        user.reset_code_expiration = None
        db.session.commit()
        return jsonify({"message": "Mot de passe mis à jour avec succès"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400