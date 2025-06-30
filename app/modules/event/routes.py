from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

from app.extensions import db
from app.modules.event.models import Event
from app.modules.event.services import (
    create_event_service,
    get_events_service,
    update_event_service,
    delete_event_service,
    valider_event_service,
    get_public_events_service
)

event_bp = Blueprint('event', __name__, url_prefix='/api/events')

# ✅ Créer un événement (authentifié)
@event_bp.route('', methods=['POST'])
@jwt_required()
def create_event():
    user_id = get_jwt_identity()
    return create_event_service(request, user_id)

# ✅ Liste tous les événements (admin/organisateur)
@event_bp.route('', methods=['GET'])
def get_events():
    return get_events_service(request)

# ✅ Modifier un événement
@event_bp.route('/<int:event_id>', methods=['PUT'])
@jwt_required()
def update_event(event_id):
    user_id = get_jwt_identity()
    return update_event_service(request, event_id, user_id)

# ✅ Supprimer un événement
@event_bp.route('/<int:event_id>', methods=['DELETE'])
@jwt_required()
def delete_event(event_id):
    user_id = get_jwt_identity()
    return delete_event_service(event_id, user_id)

# ✅ Valider un événement
@event_bp.route('/<int:event_id>/valider', methods=['PUT'])
@jwt_required()
def valider_event(event_id):
    user_id = get_jwt_identity()
    return valider_event_service(event_id, user_id)

# ✅ Récupérer les événements publics validés
@event_bp.route('/public', methods=['GET'])
def get_public_events():
    return get_public_events_service(request)

# ✅ Récupérer un événement public individuel (nouvelle route)
@event_bp.route('/public/<int:event_id>', methods=['GET'])
def get_public_event_by_id(event_id):
    event = Event.query.filter_by(id=event_id, type='public', est_valide=True).first()

    if not event:
        return jsonify({"message": "Événement non trouvé ou non accessible."}), 404

    statut = "à venir" if event.date > datetime.now() else "passé"

    event_data = {
        "id": event.id,
        "titre": event.titre,
        "description": event.description,
        "date": event.date.isoformat(),
        "lieu": event.lieu,
        "latitude": event.latitude,
        "longitude": event.longitude,
        "image_url": event.image_url,
        "type": event.type,
        "statut": statut,
        "categorie_id": event.categorie_id,
        "organisateur": {
            "id": getattr(event.organisateur, 'id', None),
            "nom": getattr(event.organisateur, 'nom', "Inconnu")
        }
    }

    return jsonify(event_data), 200
