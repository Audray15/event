from flask import request, jsonify, url_for, current_app
import smtplib
from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity,
    get_jwt,
    create_access_token,
    create_refresh_token
)
from datetime import timedelta
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

# Enregistrement
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    response = create_user_service(data)
    return jsonify(response), response.get("status", 400)

# Connexion
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

# Rafraîchissement du token
@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh_token():
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity)
    return jsonify({"access_token": access_token}), 200

# Déconnexion
@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    jti = get_jwt()["jti"]
    revoke_token(jti)
    return jsonify({"message": "Déconnexion réussie"}), 200

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """Envoie le lien de réinitialisation par email"""
    try:
        email = request.json.get('email')
        if not email:
            return jsonify({"error": "Email requis"}), 400

        user = User.query.filter_by(email=email).first()
        if not user:
            # Ne pas révéler que l'email n'existe pas
            return jsonify({"message": "Si l'email existe, un lien a été envoyé"}), 200

        # Génération du token
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        token = s.dumps(email, salt='password-reset')
        
        # Construction de l'URL complète
        reset_url = f"{request.host_url}api/auth/reset-password?token={token}"

        # Envoi SMTP direct (plus fiable que Flask-Mail)
        with smtplib.SMTP(current_app.config['MAIL_SERVER'], 
                         current_app.config['MAIL_PORT']) as server:
            server.starttls()
            server.login(current_app.config['MAIL_USERNAME'],
                        current_app.config['MAIL_PASSWORD'])
            
            message = f"""Subject: Réinitialisation de mot de passe
From: {current_app.config['MAIL_DEFAULT_SENDER']}
To: {email}

Cliquez pour réinitialiser : {reset_url} (valable 1 heure)"""
            
            server.sendmail(
                current_app.config['MAIL_DEFAULT_SENDER'],
                [email],
                message.encode('utf-8')
            )

        return jsonify({"message": "Email envoyé avec succès"}), 200

    except smtplib.SMTPAuthenticationError:
        return jsonify({
            "error": "Erreur d'authentification SMTP",
            "solution": "Vérifiez le mot de passe d'application dans .env"
        }), 503
    except Exception as e:
        current_app.logger.error(f"Erreur: {str(e)}")
        return jsonify({"error": str(e)}), 500

@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    """
    GET: Vérifie la validité du token
    POST: Réinitialise le mot de passe
    """
    token = request.args.get('token') if request.method == 'GET' else request.json.get('token')
    
    if not token:
        return jsonify({"error": "Token manquant"}), 400

    try:
        # Vérification du token
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        email = s.loads(token, salt='password-reset', max_age=3600)  # 1h expiration

        if request.method == 'GET':
            return jsonify({
                "status": "Token valide",
                "email": email,
                "reset_link": f"{request.host_url}api/auth/reset-password?token={token}"
            }), 200

        # Méthode POST
        new_password = request.json.get('password')
        if not new_password:
            return jsonify({"error": "Nouveau mot de passe requis"}), 400

        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"error": "Utilisateur non trouvé"}), 404

        user.set_password(new_password)
        db.session.commit()
        return jsonify({"message": "Mot de passe mis à jour avec succès"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Token invalide ou expiré" if "SignatureExpired" in str(e) else str(e)}), 400