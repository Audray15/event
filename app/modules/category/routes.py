from flask import request, jsonify
from flask_jwt_extended import jwt_required
from . import category_bp
from app.modules.category.services import (
    get_all_categories, get_category_by_id,
    create_category, update_category, delete_category
)
from app.modules.auth.utils import role_required

@category_bp.route('/', methods=['GET'])
@jwt_required()
def list_categories():
    categories = get_all_categories()
    return jsonify([cat.to_dict() for cat in categories]), 200

@category_bp.route('/<int:category_id>', methods=['GET'])
@jwt_required()
def get_category(category_id):
    category = get_category_by_id(category_id)
    if not category:
        return jsonify({'message': 'Catégorie non trouvée'}), 404
    return jsonify(category.to_dict()), 200

@category_bp.route('/', methods=['POST'])
@jwt_required()
@role_required(['admin', 'super_admin'])
def create_new_category():
    data = request.get_json() or {}
    nom = data.get('nom')
    description = data.get('description')

    if not nom:
        return jsonify({'message': 'Le nom est requis'}), 400

    category = create_category(nom, description)
    if category is None:
        return jsonify({'message': 'Nom de catégorie déjà utilisé'}), 409

    return jsonify(category.to_dict()), 201

@category_bp.route('/<int:category_id>', methods=['PUT', 'PATCH'])
@jwt_required()
@role_required(['admin', 'super_admin'])
def update_existing_category(category_id):
    data = request.get_json() or {}
    nom = data.get('nom')
    description = data.get('description')

    category = update_category(category_id, nom, description)
    if category is None:
        return jsonify({'message': 'Catégorie non trouvée ou nom déjà utilisé'}), 404

    return jsonify(category.to_dict()), 200

@category_bp.route('/<int:category_id>', methods=['DELETE'])
@jwt_required()
@role_required(['admin', 'super_admin'])
def delete_existing_category(category_id):
    success = delete_category(category_id)
    if not success:
        return jsonify({'message': 'Catégorie non trouvée ou suppression impossible'}), 404
    return jsonify({'message': 'Catégorie supprimée avec succès'}), 200
