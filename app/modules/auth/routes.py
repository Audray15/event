from flask import request, jsonify, url_for
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

# 🔐 Sérialiseur sécurisé pour les liens avec token
s = URLSafeTimedSerializer("clé_secrète_du_token")  # Peut aussi être app.config['SECRET_KEY']

# ✅ Enregistrement
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    response = create_user_service(data)
    return jsonify(response), response.get("status", 400)


# ✅ Connexion
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user_data, error = authenticate_user_service(data.get("email"), data.get("password"))
    
    if error:
        return jsonify({"message": error}), 401
    
    return jsonify({
        "message": "Connexion réussie.",
        "access_token": user_data["access_token"],
        "refresh_token": user_data["refresh_token"],
        "user": user_data["user"]
    }), 200


# ✅ Rafraîchissement du token
@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh_token():
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity, expires_delta=timedelta(hours=1))
    return jsonify({
        "access_token": access_token
    }), 200


# ✅ Déconnexion
@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    jti = get_jwt()["jti"]
    revoke_token(jti)
    return jsonify({"message": "Déconnexion réussie."}), 200


# ✅ Mot de passe oublié : envoi de lien par email
@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    data = request.get_json()
    email = data.get("email")

    if not email:
        return jsonify({"message": "L'email est requis."}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"message": "Aucun utilisateur trouvé avec cet email."}), 404

    # Générer le token avec expiration (ex: 10 minutes)
    token = s.dumps(email, salt='reset-password-salt')
    reset_url = url_for('auth.reset_password', token=token, _external=True)

    # Envoi email
    subject = "Réinitialisation de votre mot de passe"
    msg = Message(subject, recipients=[email])
    msg.body = f'''Bonjour {user.nom},

Vous avez demandé la réinitialisation de votre mot de passe.
Cliquez sur le lien suivant pour choisir un nouveau mot de passe (valide 10 minutes) :

{reset_url}

Si vous n'avez pas demandé cette opération, ignorez cet email.
'''
    try:
        mail.send(msg)
        return jsonify({"message": "📧 Un lien de réinitialisation a été envoyé à votre adresse email."}), 200
    except Exception as e:
        print("Erreur mail:", str(e))  # <=== Ajoute ceci pour voir l'erreur en console
        return jsonify({"message": "Erreur lors de l’envoi de l’email.", "error": str(e)}), 500


# ✅ Changement du mot de passe avec token
@auth_bp.route('/reset-password/<token>', methods=['POST'])
def reset_password(token):
    data = request.get_json()
    new_password = data.get("password")

    if not new_password:
        return jsonify({"message": "Le mot de passe est requis."}), 400

    try:
        email = s.loads(token, salt='reset-password-salt', max_age=600)  # 10 minutes
    except Exception:
        return jsonify({"message": "Le lien de réinitialisation est invalide ou expiré."}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"message": "Utilisateur non trouvé."}), 404

    user.set_password(new_password)
    db.session.commit()

    return jsonify({"message": "Mot de passe mis à jour avec succès."}), 200
