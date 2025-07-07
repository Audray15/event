from flask import request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from flask_mail import Message
from . import registration_bp
from app.utils.role_required import role_required
from app.modules.registration.models import Registration
from app.modules.event.models import Event
from app.modules.user.models import User
from app.extensions import mail
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

@registration_bp.route('', methods=['POST'])
@jwt_required()
@role_required(['user', 'organizer', 'admin', 'super_admin'])
def register_to_event():
    data = request.get_json()
    user_id = int(get_jwt_identity())
    event_id = data.get('event_id')

    if not event_id:
        return jsonify({"message": "Le champ 'event_id' est requis."}), 400

    new_db_session = current_app.db_session()
    
    try:
        # Récupérer l'événement
        event = new_db_session.get(Event, event_id)
        if not event:
            return jsonify({"message": "Événement non trouvé."}), 404

        # Vérifier si déjà inscrit
        existing_registration = new_db_session.query(Registration).filter_by(
            user_id=user_id,
            event_id=event_id
        ).first()
        if existing_registration:
            return jsonify({"message": "Vous êtes déjà inscrit à cet événement."}), 409

        # Récupérer l'utilisateur
        user = new_db_session.get(User, user_id)
        if not user:
            return jsonify({"message": "Utilisateur non trouvé."}), 404

        # Créer l'inscription
        registration = Registration(
            user_id=user_id,
            event_id=event_id
        )
        new_db_session.add(registration)
        new_db_session.commit()
        
        # Envoyer l'email de confirmation - Version corrigée et simplifiée
        try:
            # Formater les dates
            event_date = event.date.strftime('%d/%m/%Y à %H:%M') if event.date else 'Date non spécifiée'
            created_at = registration.created_at.strftime('%d/%m/%Y à %H:%M')
            
            # Construire le corps du message
            body = (
                f"Bonjour {user.nom},\n\n"
                f"Confirmation de votre inscription à l'événement :\n"
                f"• Événement: {event.titre}\n"
                f"• Date: {event_date}\n"
                f"• Lieu: {event.lieu}\n"
                f"• ID Inscription: {registration.id}\n"
                f"• Date d'inscription: {created_at}\n\n"
                f"Merci pour votre participation !\n\n"
                f"Cordialement,\n"
                f"L'équipe des événements"
            )
            
            # Création du message avec les paramètres positionnels corrects
            msg = Message(
                f"Confirmation d'inscription - {event.titre}",  # Sujet
                recipients=[user.email],  # Destinataires
                body=body  # Corps du message
            )
            
            mail.send(msg)  # Envoi via l'extension mail
            
            logger.info(f"Email de confirmation envoyé à {user.email}")
            
        except Exception as email_error:
            logger.error(f"Erreur envoi email: {str(email_error)}", exc_info=True)
        
        return jsonify({
            "message": "Inscription réussie. Un email de confirmation a été envoyé.",
            "registration_id": registration.id,
            "event_title": event.titre,
            "user_email": user.email
        }), 201
        
    except Exception as e:
        logger.error(f"Erreur inscription: {str(e)}", exc_info=True)
        new_db_session.rollback()
        return jsonify({"message": "Erreur serveur lors de l'inscription"}), 500
    finally:
        new_db_session.close()

@registration_bp.route('/event/<int:event_id>', methods=['DELETE'])
@jwt_required()
def unregister_from_event(event_id):
    user_id = int(get_jwt_identity())
    claims = get_jwt()
    user_role = claims.get("role")
    
    logger.info(f"Désinscription demandée: user_id={user_id}, event_id={event_id}")

    new_db_session = current_app.db_session()
    
    try:
        event = new_db_session.get(Event, event_id)
        if not event:
            return jsonify({"message": "Événement non trouvé."}), 404

        registration = new_db_session.query(Registration).filter_by(
            user_id=user_id,
            event_id=event_id
        ).first()
        
        if not registration:
            return jsonify({"message": "Vous n'êtes pas inscrit à cet événement."}), 404

        is_admin = user_role in ["admin", "super_admin"]
        if registration.user_id != user_id and not is_admin:
            return jsonify({"message": "Permission refusée pour cette action."}), 403

        new_db_session.delete(registration)
        new_db_session.commit()
        
        return jsonify({
            "message": "Désinscription réussie.",
            "event_title": event.titre
        }), 200
    except Exception as e:
        logger.error(f"Erreur désinscription: {str(e)}", exc_info=True)
        new_db_session.rollback()
        return jsonify({"message": "Erreur lors de la désinscription"}), 500
    finally:
        new_db_session.close()

@registration_bp.route('/<int:registration_id>', methods=['DELETE'])
@jwt_required()
@role_required(['admin', 'super_admin'])
def admin_delete_registration(registration_id):
    new_db_session = current_app.db_session()
    
    try:
        registration = new_db_session.get(Registration, registration_id)
        if not registration:
            return jsonify({"message": "Inscription non trouvée."}), 404

        event_title = registration.event.titre if registration.event else "Inconnu"
        new_db_session.delete(registration)
        new_db_session.commit()
        return jsonify({
            "message": "Inscription supprimée avec succès.",
            "event_title": event_title
        }), 200
    except Exception as e:
        new_db_session.rollback()
        return jsonify({"message": "Erreur lors de la suppression"}), 500
    finally:
        new_db_session.close()

@registration_bp.route('', methods=['GET'])
@jwt_required()
@role_required(['user', 'organizer', 'admin', 'super_admin'])
def get_user_registrations():
    user_id = int(get_jwt_identity())
    claims = get_jwt()
    role = claims.get("role")

    new_db_session = current_app.db_session()
    
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
                "event_lieu": event.lieu,
                "registered_at": reg.created_at.isoformat()
            })

        return jsonify(results), 200
    except Exception as e:
        logger.error(f"Erreur récupération inscriptions: {str(e)}")
        return jsonify({"message": "Erreur serveur"}), 500
    finally:
        new_db_session.close()

@registration_bp.route('/event/<int:event_id>', methods=['GET'])
@jwt_required()
@role_required(['organizer', 'admin', 'super_admin'])
def get_event_registrations(event_id):
    current_user_id = int(get_jwt_identity())
    claims = get_jwt()
    user_role = claims.get("role")

    new_db_session = current_app.db_session()
    
    try:
        event = new_db_session.get(Event, event_id)
        if not event:
            return jsonify({"message": "Événement non trouvé."}), 404

        if user_role == "organizer" and event.organisateur_id != current_user_id:
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
        return jsonify({"message": "Erreur serveur"}), 500
    finally:
        new_db_session.close()