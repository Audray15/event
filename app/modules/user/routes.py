from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from .services import (
    get_all_users, get_user_by_id, create_user,
    update_user, delete_user, change_password_service
)
from app.modules.auth.utils import role_required, is_admin

user_bp = Blueprint('user_bp', __name__, url_prefix='/api/users')

@user_bp.route('/', methods=['GET'])
@jwt_required()
@role_required(['admin', 'super_admin'])
def list_users():
    users = get_all_users()
    return jsonify([user.to_dict() for user in users]), 200

@user_bp.route('/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    current_user_id = get_jwt_identity()
    user = get_user_by_id(user_id)
    
    if not user:
        return jsonify({'message': 'Utilisateur non trouvé'}), 404

    # Autoriser l'accès à son propre compte ou aux admins
    if user.id != int(current_user_id) and not is_admin():
        return jsonify({
            'message': 'Accès refusé : vous ne pouvez accéder qu\'à votre propre compte'
        }), 403

    return jsonify(user.to_dict()), 200

@user_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    user_id = get_jwt_identity()
    user = get_user_by_id(user_id)
    if not user:
        return jsonify({'message': 'Utilisateur non trouvé'}), 404
    return jsonify(user.to_dict()), 200

@user_bp.route('/', methods=['POST'])
@jwt_required()
@role_required(['admin', 'super_admin'])
def add_user():
    data = request.get_json()
    if not data:
        return jsonify({'message': 'Requête JSON invalide ou manquante'}), 400

    required_fields = ['nom', 'email', 'password']
    if not all(field in data and data[field] for field in required_fields):
        return jsonify({'message': 'Champs requis manquants ou vides'}), 400

    user = create_user(
        nom=data['nom'],
        email=data['email'],
        password=data['password'],
        telephone=data.get('telephone'),
        role=data.get('role', 'user')
    )
    if user is None:
        return jsonify({'message': 'Email déjà utilisé'}), 409
    return jsonify(user.to_dict()), 201

@user_bp.route('/<int:user_id>', methods=['PUT', 'PATCH'])
@jwt_required()
def edit_user(user_id):
    data = request.get_json()
    if not data:
        return jsonify({'message': 'Requête JSON invalide ou manquante'}), 400

    current_user_id = get_jwt_identity()
    user = get_user_by_id(user_id)
    
    if not user:
        return jsonify({'message': 'Utilisateur non trouvé'}), 404

    # Autoriser la modification de son propre compte ou par un admin
    if user.id != int(current_user_id) and not is_admin():
        return jsonify({
            'message': 'Accès refusé : vous ne pouvez modifier que votre propre compte'
        }), 403

    # Empêcher la modification de certains champs
    for forbidden in ['id', 'password']:
        data.pop(forbidden, None)

    # Seuls les admins peuvent modifier le rôle
    if 'role' in data and not is_admin():
        data.pop('role')

    updated_user = update_user(user_id, **data)
    if not updated_user:
        return jsonify({'message': 'Erreur lors de la mise à jour'}), 400
        
    return jsonify(updated_user.to_dict()), 200

@user_bp.route('/<int:user_id>', methods=['DELETE'])
@jwt_required()
def remove_user(user_id):
    current_user_id = get_jwt_identity()
    user = get_user_by_id(user_id)
    
    if not user:
        return jsonify({'message': 'Utilisateur non trouvé'}), 404

    # Autoriser la suppression de son propre compte ou par un admin
    if user.id != int(current_user_id) and not is_admin():
        return jsonify({
            'message': 'Accès refusé : vous ne pouvez supprimer que votre propre compte'
        }), 403

    success = delete_user(user_id)
    if not success:
        return jsonify({'message': 'Erreur lors de la suppression'}), 500
        
    return jsonify({'message': 'Utilisateur supprimé avec succès'}), 200

@user_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    user_id = get_jwt_identity()
    data = request.get_json()

    if not data or 'old_password' not in data or 'new_password' not in data:
        return jsonify({"message": "Les champs 'old_password' et 'new_password' sont requis."}), 400

    old_password = data['old_password']
    new_password = data['new_password']

    result, error = change_password_service(user_id, old_password, new_password)
    if error:
        return jsonify({"message": error}), 400

    return jsonify({"message": "Mot de passe changé avec succès."}), 200