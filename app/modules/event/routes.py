from flask import Blueprint, request, jsonify, current_app, send_from_directory, url_for
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from sqlalchemy.orm import joinedload, load_only

from app.extensions import db
from app.modules.event.models import Event
from app.modules.user.models import User
from app.modules.event.services import (
    create_event_service,
    get_events_service,
    update_event_service,
    delete_event_service,
    valider_event_service,
    get_public_events_service
)

event_bp = Blueprint('event', __name__, url_prefix='/api/events')

@event_bp.route('', methods=['POST'])
@jwt_required()
def create_event():
    user_id = get_jwt_identity()
    return create_event_service(request, user_id)

@event_bp.route('', methods=['GET'])
@jwt_required()  # Maintenant protégée par JWT
def get_events():
    user_id = get_jwt_identity()
    return get_events_service(request, user_id)

@event_bp.route('/<int:event_id>', methods=['PUT'])
@jwt_required()
def update_event(event_id):
    user_id = get_jwt_identity()
    return update_event_service(request, event_id, user_id)

@event_bp.route('/<int:event_id>', methods=['DELETE'])
@jwt_required()
def delete_event(event_id):
    user_id = get_jwt_identity()
    return delete_event_service(event_id, user_id)

@event_bp.route('/<int:event_id>/valider', methods=['PATCH'])
@jwt_required()
def valider_event(event_id):
    user_id = get_jwt_identity()
    return valider_event_service(event_id, user_id)

@event_bp.route('/public', methods=['GET'])
def get_public_events():
    return get_public_events_service(request)

@event_bp.route('/public/<int:event_id>', methods=['GET'])
def get_public_event_by_id(event_id):
    event = Event.query.options(
        joinedload(Event.organisateur).load_only(User.id, User.nom, User.email)
    ).filter_by(id=event_id, type='public', est_valide=True).first()

    if not event:
        return jsonify({"message": "Événement non trouvé ou non accessible."}), 404

    statut = "à venir" if event.date > datetime.now() else "passé"

    image_url = url_for('event.get_image', filename=event.image_url, _external=True) if event.image_url else None

    if event.organisateur:
        organisateur_info = {
            "id": event.organisateur.id,
            "nom": event.organisateur.nom,
            "email": event.organisateur.email
        }
    else:
        organisateur_info = {
            "id": None,
            "nom": "Organisateur supprimé",
            "email": ""
        }

    event_data = {
        "id": event.id,
        "titre": event.titre,
        "description": event.description,
        "date": event.date.isoformat(),
        "lieu": event.lieu,
        "latitude": event.latitude,
        "longitude": event.longitude,
        "image_url": image_url,
        "type": event.type,
        "statut": statut,
        "categorie_id": event.categorie_id,
        "organisateur": organisateur_info
    }

    return jsonify(event_data), 200

@event_bp.route('/images/<filename>')
def get_image(filename):
    upload_folder = current_app.config['UPLOAD_FOLDER']
    return send_from_directory(upload_folder, filename)