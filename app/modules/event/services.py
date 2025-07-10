from flask import request, jsonify, current_app, url_for
from datetime import datetime
from app.extensions import db
from app.modules.event.models import Event
from werkzeug.utils import secure_filename
import os
import logging
import uuid

logger = logging.getLogger(__name__)

def normalize_event_type(type_str):
    if not type_str:
        return None
    type_str = type_str.strip().lower()
    mapping = {
        'privé': 'prive',
        'private': 'prive',
        'priv': 'prive',
        'public': 'public',
        'publique': 'public'
    }
    return mapping.get(type_str, type_str)

def create_event_service(request, user_id):
    try:
        try:
            user_id_int = int(user_id)
        except ValueError:
            return jsonify({"message": "ID utilisateur invalide."}), 400

        titre = request.form.get('titre')
        date_str = request.form.get('date')
        lieu = request.form.get('lieu')
        categorie_id = request.form.get('categorie_id')

        if not all([titre, date_str, lieu, categorie_id]):
            return jsonify({"message": "Les champs titre, date, lieu et categorie_id sont requis."}), 400

        try:
            date = datetime.fromisoformat(date_str)
        except ValueError:
            return jsonify({"message": "Le format de date est invalide. Utilisez YYYY-MM-DDTHH:MM:SS"}), 400

        description = request.form.get('description')

        try:
            latitude = float(request.form.get('latitude', 0))
            longitude = float(request.form.get('longitude', 0))
        except ValueError:
            latitude = 0
            longitude = 0

        type_evt = request.form.get('type', 'public')
        normalized_type = normalize_event_type(type_evt) or 'public'

        est_valide_str = request.form.get('est_valide', 'false').lower()
        est_valide = est_valide_str in ['true', '1', 'yes', 'vrai', 'oui']

        image = request.files.get('image')
        image_filename = None
        if image and image.filename != '':
            max_size = current_app.config.get('MAX_CONTENT_LENGTH', 10 * 1024 * 1024)
            if image.content_length > max_size:
                return jsonify({
                    "message": f"La taille de l'image dépasse la limite autorisée ({max_size//1024//1024}MB)"
                }), 413

            filename = secure_filename(image.filename)
            ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
            unique_filename = f"{uuid.uuid4().hex}.{ext}" if ext else uuid.uuid4().hex

            upload_folder = current_app.config['UPLOAD_FOLDER']
            os.makedirs(upload_folder, exist_ok=True)
            image_path = os.path.join(upload_folder, unique_filename)
            image.save(image_path)
            image_filename = unique_filename

        event = Event(
            titre=titre,
            description=description,
            date=date,
            lieu=lieu,
            latitude=latitude,
            longitude=longitude,
            image_url=image_filename,
            type=normalized_type,
            est_valide=est_valide,
            categorie_id=int(categorie_id),
            organisateur_id=user_id_int
        )

        db.session.add(event)
        db.session.commit()

        image_url = url_for('event.get_image', filename=event.image_url, _external=True) if event.image_url else None

        return jsonify({
            "message": "Événement créé avec succès.",
            "event_id": event.id,
            "type": normalized_type,
            "est_valide": est_valide,
            "image_url": image_url
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur création événement: {str(e)}", exc_info=True)
        return jsonify({"message": f"Erreur lors de la création : {str(e)}"}), 500

def get_events_service(request):
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        type_filter = request.args.get('type')
        categorie_id = request.args.get('categorie_id')

        query = Event.query

        if type_filter:
            normalized_type = normalize_event_type(type_filter)
            if normalized_type:
                query = query.filter_by(type=normalized_type)

        if categorie_id:
            try:
                categorie_id_int = int(categorie_id)
                query = query.filter_by(categorie_id=categorie_id_int)
            except ValueError:
                pass

        events = query.paginate(page=page, per_page=per_page, error_out=False)
        now = datetime.now()

        result = []
        for event in events.items:
            statut = "en attente"
            if event.est_valide:
                statut = "à venir" if event.date > now else "passé"

            image_url = url_for('event.get_image', filename=event.image_url, _external=True) if event.image_url else None

            result.append({
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
                "est_valide": event.est_valide,
                "categorie_id": event.categorie_id,
                "organisateur_id": event.organisateur_id
            })

        return jsonify({
            "events": result,
            "total": events.total,
            "page": events.page,
            "pages": events.pages
        }), 200

    except Exception as e:
        logger.error(f"Erreur récupération événements: {str(e)}", exc_info=True)
        return jsonify({"message": f"Erreur lors de la récupération des événements: {str(e)}"}), 500

def get_public_events_service(request):
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))

        query = Event.query.filter_by(type='public', est_valide=True)
        events = query.paginate(page=page, per_page=per_page, error_out=False)
        now = datetime.now()

        result = []
        for event in events.items:
            statut = "à venir" if event.date > now else "passé"

            image_url = url_for('event.get_image', filename=event.image_url, _external=True) if event.image_url else None

            result.append({
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
                "organisateur": {
                    "id": getattr(event.organisateur, 'id', None),
                    "nom": getattr(event.organisateur, 'nom', "Inconnu"),
                    "email": getattr(event.organisateur, 'email', "Inconnu")
                }
            })

        return jsonify({
            "events": result,
            "total": events.total,
            "page": events.page,
            "pages": events.pages
        }), 200

    except Exception as e:
        logger.error(f"Erreur récupération événements publics: {str(e)}", exc_info=True)
        return jsonify({"message": f"Erreur lors de la récupération des événements publics: {str(e)}"}), 500

def update_event_service(request, event_id, user_id):
    event = Event.query.get_or_404(event_id)

    try:
        user_id_int = int(user_id)
    except ValueError:
        return jsonify({"message": "ID utilisateur invalide."}), 400

    if event.organisateur_id != user_id_int:
        return jsonify({"message": "Non autorisé à modifier cet événement."}), 403

    try:
        data = request.form.to_dict()
        files = request.files

        for key in ['titre', 'description', 'lieu']:
            if key in data:
                setattr(event, key, data[key])

        if 'type' in data:
            normalized_type = normalize_event_type(data['type'])
            if normalized_type:
                setattr(event, 'type', normalized_type)

        if 'categorie_id' in data:
            try:
                event.categorie_id = int(data['categorie_id'])
            except ValueError:
                pass

        if 'date' in data:
            try:
                event.date = datetime.fromisoformat(data['date'])
            except ValueError:
                return jsonify({"message": "Format de date invalide. Utilisez YYYY-MM-DDTHH:MM:SS"}), 400

        if 'latitude' in data:
            try:
                event.latitude = float(data['latitude'])
            except ValueError:
                pass

        if 'longitude' in data:
            try:
                event.longitude = float(data['longitude'])
            except ValueError:
                pass

        if 'image' in files:
            image = files['image']
            if image.filename != '':
                max_size = current_app.config.get('MAX_CONTENT_LENGTH', 10 * 1024 * 1024)
                if image.content_length > max_size:
                    return jsonify({
                        "message": f"La taille de l'image dépasse la limite autorisée ({max_size//1024//1024}MB)"
                    }), 413

                if event.image_url:
                    try:
                        upload_folder = current_app.config['UPLOAD_FOLDER']
                        old_image_path = os.path.join(upload_folder, event.image_url)
                        if os.path.exists(old_image_path):
                            os.remove(old_image_path)
                    except Exception as e:
                        logger.error(f"Erreur suppression ancienne image: {str(e)}")

                filename = secure_filename(image.filename)
                ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
                unique_filename = f"{uuid.uuid4().hex}.{ext}" if ext else uuid.uuid4().hex

                upload_folder = current_app.config['UPLOAD_FOLDER']
                os.makedirs(upload_folder, exist_ok=True)
                image_path = os.path.join(upload_folder, unique_filename)
                image.save(image_path)
                event.image_url = unique_filename

        if 'est_valide' in data:
            est_valide_str = data['est_valide'].lower()
            event.est_valide = est_valide_str in ['true', '1', 'yes', 'vrai', 'oui']

        db.session.commit()

        image_url = url_for('event.get_image', filename=event.image_url, _external=True) if event.image_url else None

        return jsonify({
            "message": "Événement mis à jour avec succès.",
            "type": event.type,
            "est_valide": event.est_valide,
            "image_url": image_url
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur mise à jour événement {event_id}: {str(e)}", exc_info=True)
        return jsonify({"message": f"Erreur lors de la mise à jour : {str(e)}"}), 500

def delete_event_service(event_id, user_id):
    event = Event.query.get_or_404(event_id)

    try:
        user_id_int = int(user_id)
    except ValueError:
        return jsonify({"message": "ID utilisateur invalide."}), 400

    if event.organisateur_id != user_id_int:
        return jsonify({"message": "Non autorisé à supprimer cet événement."}), 403

    try:
        if event.image_url:
            try:
                upload_folder = current_app.config['UPLOAD_FOLDER']
                image_path = os.path.join(upload_folder, event.image_url)
                if os.path.exists(image_path):
                    os.remove(image_path)
            except Exception as e:
                logger.error(f"Erreur suppression image: {str(e)}")

        db.session.delete(event)
        db.session.commit()
        return jsonify({"message": "Événement supprimé avec succès."}), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur suppression événement {event_id}: {str(e)}", exc_info=True)
        return jsonify({"message": f"Erreur lors de la suppression : {str(e)}"}), 500

def valider_event_service(event_id, user_id):
    event = Event.query.get_or_404(event_id)

    try:
        user_id_int = int(user_id)
    except ValueError:
        return jsonify({"message": "ID utilisateur invalide."}), 400

    if event.organisateur_id != user_id_int:
        return jsonify({"message": "Non autorisé à valider cet événement."}), 403

    try:
        event.est_valide = True
        db.session.commit()
        return jsonify({
            "message": "Événement validé avec succès.",
            "est_valide": True
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur validation événement {event_id}: {str(e)}", exc_info=True)
        return jsonify({"message": f"Erreur lors de la validation : {str(e)}"}), 500
