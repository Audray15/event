from flask import jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from . import dashboard_bp
from .services import get_global_stats, get_organizer_stats, get_user_stats
from app.utils.role_required import role_required

@dashboard_bp.route('/api/dashboard/global', methods=['GET'])
@jwt_required()
@role_required(['admin', 'super_admin'])
def global_dashboard():
    stats = get_global_stats()
    return jsonify(stats), 200

@dashboard_bp.route('/api/dashboard/organizer', methods=['GET'])
@jwt_required()
@role_required(['organizer'])
def organizer_dashboard():
    user_id = get_jwt_identity()
    stats = get_organizer_stats(user_id)
    return jsonify(stats), 200

@dashboard_bp.route('/api/dashboard/user', methods=['GET'])
@jwt_required()
@role_required(['user', 'organizer', 'admin', 'super_admin'])
def user_dashboard():
    user_id = get_jwt_identity()
    stats = get_user_stats(user_id)
    return jsonify(stats), 200