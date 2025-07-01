from flask import request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from . import registration_bp
from app.utils.role_required import role_required
from app.modules.registration.models import Registration
from app.modules.event.models import Event
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

ROLE_ALIASES = {
    "user": "utilisateur",
    "organizer": "organisateur",
    "visitor": "visiteur"
}

@registration_bp.route('', methods=['POST'])
@jwt_required()
@role_required(['utilisateur', 'organisateur', 'admin', 'super_admin'])
def register_to_event():
    data = request.get_json()
    user_id = int(get_jwt_identity())
    event_id = data.get('event_id')

    if not event_id:
        return jsonify({"message": "Le champ 'event_id' est requis."}), 400

    new_db_session = current_app.get_new_session()
    
    try:
        event = new_db_session.get(Event, event_id)
        if not event:
            return jsonify({"message": "Événement non trouvé."}), 404

        # Vérifier si l'utilisateur est déjà inscrit
        exists = new_db_session.query(
            new_db_session.query(Registration)
            .filter_by(user_id=user_id, event_id=event_id)
            .exists()
        ).scalar()

        if exists:
            return jsonify({"message": "Vous êtes déjà inscrit à cet événement."}), 409

        # Création avec date explicite
        registration = Registration(
            user_id=user_id,
            event_id=event_id,
            created_at=datetime.utcnow()
        )
        new_db_session.add(registration)
        new_db_session.commit()
        
        # Vérification de la persistance
        persisted = new_db_session.get(Registration, registration.id)
        if not persisted:
            logger.error("Échec de la persistance de l'inscription")
            return jsonify({"message": "Erreur système lors de l'inscription"}), 500

        return jsonify({
            "message": "Inscription réussie à l'événement.",
            "registration_id": registration.id
        }), 201
    except Exception as e:
        logger.error(f"Erreur inscription: {str(e)}", exc_info=True)
        new_db_session.rollback()
        return jsonify({"message": f"Erreur serveur: {str(e)}"}), 500
    finally:
        new_db_session.close()

@registration_bp.route('/event/<int:event_id>', methods=['DELETE'])
@jwt_required()
def unregister_from_event(event_id):
    user_id = int(get_jwt_identity())
    claims = get_jwt()
    user_role = claims.get("role")
    
    logger.info(f"Désinscription demandée: user_id={user_id}, event_id={event_id}")

    new_db_session = current_app.get_new_session()
    
    try:
        # Vérifier que l'événement existe
        event = new_db_session.get(Event, event_id)
        if not event:
            logger.warning(f"Événement {event_id} non trouvé")
            return jsonify({"message": "Événement non trouvé."}), 404

        # Recherche directe
        registration = new_db_session.query(Registration).filter(
            Registration.user_id == user_id,
            Registration.event_id == event_id
        ).first()
        
        if not registration:
            logger.warning(f"Aucune inscription trouvée: user_id={user_id}, event_id={event_id}")
            return jsonify({"message": "Vous n'êtes pas inscrit à cet événement."}), 404

        # Vérifier les permissions
        is_admin = user_role in ["admin", "super_admin"]
        if registration.user_id != user_id and not is_admin:
            logger.warning(f"Permission refusée: user_id={user_id} essaie de supprimer inscription {registration.id}")
            return jsonify({"message": "Permission refusée pour cette action."}), 403

        # Suppression
        new_db_session.delete(registration)
        new_db_session.commit()
        logger.info(f"Inscription {registration.id} supprimée avec succès")
        return jsonify({"message": "Désinscription réussie."}), 200
    except Exception as e:
        logger.error(f"Erreur désinscription: {str(e)}", exc_info=True)
        new_db_session.rollback()
        return jsonify({
            "message": f"Erreur lors de la désinscription: {str(e)}"
        }), 500
    finally:
        new_db_session.close()

@registration_bp.route('/<int:registration_id>', methods=['DELETE'])
@jwt_required()
@role_required(['admin', 'super_admin'])
def admin_delete_registration(registration_id):
    new_db_session = current_app.get_new_session()
    
    try:
        registration = new_db_session.get(Registration, registration_id)
        if not registration:
            return jsonify({"message": "Inscription non trouvée."}), 404

        new_db_session.delete(registration)
        new_db_session.commit()
        return jsonify({"message": "Inscription supprimée avec succès."}), 200
    except Exception as e:
        new_db_session.rollback()
        return jsonify({"message": f"Erreur lors de la suppression: {str(e)}"}), 500
    finally:
        new_db_session.close()

@registration_bp.route('', methods=['GET'])
@jwt_required()
@role_required(['utilisateur', 'organisateur', 'admin', 'super_admin'])
def get_user_registrations():
    user_id = int(get_jwt_identity())
    claims = get_jwt()
    role = ROLE_ALIASES.get(claims.get("role"), claims.get("role"))

    new_db_session = current_app.get_new_session()
    
    try:
        if role in ["admin", "super_admin"] and request.args.get("all") == "1":
            registrations = new_db_session.query(Registration).all()
        else:
            registrations = new_db_session.query(Registration).filter_by(user_id=user_id).all()

        results = []
        for reg in registrations:
            event = reg.event
            results.append({
                "registration_id": reg.id,
                "event_id": event.id,
                "event_title": event.titre,
                "event_date": event.date.strftime('%Y-%m-%d') if event.date else None,
                # CORRECTION: Ajout du champ event_lieu
                "event_lieu": event.lieu,
                "registered_at": reg.created_at.isoformat()
            })

        return jsonify(results), 200
    except Exception as e:
        logger.error(f"Erreur récupération inscriptions: {str(e)}")
        return jsonify({"message": f"Erreur serveur: {str(e)}"}), 500
    finally:
        new_db_session.close()

@registration_bp.route('/event/<int:event_id>', methods=['GET'])
@jwt_required()
@role_required(['organisateur', 'admin', 'super_admin'])
def get_event_registrations(event_id):
    current_user_id = int(get_jwt_identity())
    claims = get_jwt()
    role = ROLE_ALIASES.get(claims.get("role"), claims.get("role"))

    new_db_session = current_app.get_new_session()
    
    try:
        event = new_db_session.get(Event, event_id)
        if not event:
            return jsonify({"message": "Événement non trouvé."}), 404

        if role == "organisateur" and event.organisateur_id != current_user_id:
            return jsonify({"message": "Accès non autorisé aux inscriptions."}), 403

        registrations = new_db_session.query(Registration).filter_by(event_id=event_id).all()

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
    except Exception as e:
        logger.error(f"Erreur récupération inscriptions: {str(e)}")
        return jsonify({"message": f"Erreur serveur: {str(e)}"}), 500
    finally:
        new_db_session.close()