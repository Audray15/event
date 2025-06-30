from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from . import registration_bp
from app.utils.role_required import role_required
from app.modules.registration.models import Registration
from app.modules.event.models import Event
from app.modules.registration import services as registration_service

# 🔸 S'inscrire à un événement
@registration_bp.route('', methods=['POST'])
@jwt_required()
@role_required(['utilisateur', 'organisateur', 'admin', 'super_admin'])
def register_to_event():
    data = request.get_json()
    user_id = get_jwt_identity()
    event_id = data.get('event_id')

    if not event_id:
        return jsonify({"message": "Le champ 'event_id' est requis."}), 400

    event = Event.query.get(event_id)
    if not event:
        return jsonify({"message": "Événement non trouvé."}), 404

    if registration_service.is_user_registered(user_id, event_id):
        return jsonify({"message": "Vous êtes déjà inscrit à cet événement."}), 409

    registration_service.create_registration(user_id, event_id)
    return jsonify({"message": "Inscription réussie à l'événement."}), 201

# 🔸 Se désinscrire (ou suppression par admin)
@registration_bp.route('/<int:registration_id>', methods=['DELETE'])
@jwt_required()
@role_required(['utilisateur', 'organisateur', 'admin', 'super_admin'])
def unregister_from_event(registration_id):
    user_id = get_jwt_identity()
    claims = get_jwt()

    registration = Registration.query.get_or_404(registration_id)

    # Normaliser rôle avec alias (même principe que dans role_required.py)
    role_aliases = {
        "user": "utilisateur",
        "organizer": "organisateur",
        "visitor": "visiteur"
    }
    user_role = role_aliases.get(claims.get("role"), claims.get("role"))

    if user_role not in ["admin", "super_admin"] and registration.user_id != user_id:
        return jsonify({"message": "Vous n'avez pas la permission de supprimer cette inscription."}), 403

    registration_service.delete_registration(registration)
    return jsonify({"message": "Désinscription réussie."}), 200

# 🔸 Voir SES inscriptions
@registration_bp.route('', methods=['GET'])
@jwt_required()
@role_required(['utilisateur', 'organisateur', 'admin', 'super_admin'])
def get_user_registrations():
    user_id = get_jwt_identity()
    claims = get_jwt()

    role_aliases = {
        "user": "utilisateur",
        "organizer": "organisateur",
        "visitor": "visiteur"
    }
    user_role = role_aliases.get(claims.get("role"), claims.get("role"))

    if user_role in ["admin", "super_admin"] and request.args.get("all") == "1":
        registrations = Registration.query.all()
    else:
        registrations = registration_service.get_user_registrations(user_id)

    results = []
    for reg in registrations:
        event = reg.event
        results.append({
            "registration_id": reg.id,
            "event_id": event.id,
            "event_title": event.titre,
            "event_date": event.date.strftime('%Y-%m-%d') if event.date else None,
            "registered_at": reg.created_at.isoformat()
        })

    return jsonify(results), 200

# 🔸 Voir les inscrits à UN événement
@registration_bp.route('/event/<int:event_id>', methods=['GET'])
@jwt_required()
@role_required(['organisateur', 'admin', 'super_admin'])
def get_event_registrations(event_id):
    current_user_id = get_jwt_identity()
    claims = get_jwt()

    role_aliases = {
        "user": "utilisateur",
        "organizer": "organisateur",
        "visitor": "visiteur"
    }
    user_role = role_aliases.get(claims.get("role"), claims.get("role"))

    event = Event.query.get_or_404(event_id)

    if user_role == "organisateur" and event.organisateur_id != current_user_id:
        return jsonify({"message": "Vous n'avez pas la permission de consulter les inscriptions à cet événement."}), 403

    registrations = registration_service.get_event_registrations(event_id)

    results = []
    for reg in registrations:
        user = reg.user
        results.append({
            "registration_id": reg.id,
            "user_id": user.id,
            "user_name": user.nom,
            "user_email": user.email,
            "registered_at": reg.created_at.isoformat()
        })

    return jsonify({
        "event_id": event.id,
        "event_titre": event.titre,
        "total_registrations": len(results),
        "registrations": results
    }), 200
