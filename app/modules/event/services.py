from flask import request, jsonify, current_app
from datetime import datetime
from app.extensions import db
from app.modules.event.models import Event
from werkzeug.utils import secure_filename
import os
import logging

# Configuration du logger
logger = logging.getLogger(__name__)

# Fonction utilitaire pour normaliser le type d'événement
def normalize_event_type(type_str):
    """Normalise les différentes orthographes des types d'événement"""
    if not type_str:
        return None
    
    type_str = type_str.strip().lower()
    
    # Mapper les variantes vers les valeurs standard
    mapping = {
        'privé': 'prive',
        'private': 'prive',
        'priv': 'prive',
        'public': 'public',
        'publique': 'public'
    }
    
    # Retourner la valeur mappée ou la valeur d'origine
    return mapping.get(type_str, type_str)

# ✅ Créer un événement (image + données formulaire)
def create_event_service(request, user_id):
    try:
        # Convertir l'ID utilisateur en entier
        try:
            user_id_int = int(user_id)
        except ValueError:
            return jsonify({"message": "ID utilisateur invalide."}), 400

        # Récupération des champs du formulaire
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
        
        # Gestion des coordonnées géographiques
        try:
            latitude = float(request.form.get('latitude', 0))
            longitude = float(request.form.get('longitude', 0))
        except ValueError:
            latitude = 0
            longitude = 0
        
        # Normalisation du type d'événement
        type_evt = request.form.get('type', 'public')
        normalized_type = normalize_event_type(type_evt) or 'public'
        
        # Gestion du statut de validation
        est_valide_str = request.form.get('est_valide', 'false').lower()
        est_valide = est_valide_str in ['true', '1', 'yes', 'vrai', 'oui']

        # Traitement de l'image
        image = request.files.get('image')
        image_url = None
        if image and image.filename != '':
            filename = secure_filename(image.filename)
            upload_folder = current_app.config.get('UPLOAD_FOLDER', 'static/uploads')
            os.makedirs(upload_folder, exist_ok=True)
            image_path = os.path.join(upload_folder, filename)
            image.save(image_path)
            image_url = f"/{image_path.replace(os.sep, '/')}"

        # Création de l'événement
        event = Event(
            titre=titre,
            description=description,
            date=date,
            lieu=lieu,
            latitude=latitude,
            longitude=longitude,
            image_url=image_url,
            type=normalized_type,
            est_valide=est_valide,
            categorie_id=int(categorie_id),
            organisateur_id=user_id_int
        )

        db.session.add(event)
        db.session.commit()

        return jsonify({
            "message": "Événement créé avec succès.",
            "event_id": event.id,
            "type": normalized_type,
            "est_valide": est_valide
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur création événement: {str(e)}", exc_info=True)
        return jsonify({"message": f"Erreur lors de la création : {str(e)}"}), 500

# ✅ Récupérer tous les événements (admin/organisateur)
def get_events_service(request):
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        type_filter = request.args.get('type')
        categorie_id = request.args.get('categorie_id')

        query = Event.query
        
        # Filtrage par type
        if type_filter:
            normalized_type = normalize_event_type(type_filter)
            if normalized_type:
                query = query.filter_by(type=normalized_type)
        
        # Filtrage par catégorie
        if categorie_id:
            try:
                categorie_id_int = int(categorie_id)
                query = query.filter_by(categorie_id=categorie_id_int)
            except ValueError:
                pass  # Ignore si conversion échoue

        # Pagination et exécution de la requête
        events = query.paginate(page=page, per_page=per_page, error_out=False)
        now = datetime.now()

        # Construction des résultats
        result = []
        for event in events.items:
            statut = "en attente"
            if event.est_valide:
                statut = "à venir" if event.date > now else "passé"

            result.append({
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

# ✅ Récupérer les événements publics (visiteurs)
def get_public_events_service(request):
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))

        # Filtre pour événements publics validés
        query = Event.query.filter_by(type='public', est_valide=True)
        events = query.paginate(page=page, per_page=per_page, error_out=False)
        now = datetime.now()

        # Construction des résultats
        result = []
        for event in events.items:
            statut = "à venir" if event.date > now else "passé"

            result.append({
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

# ✅ Mettre à jour un événement (gère les données form-data, y compris l'image)
def update_event_service(request, event_id, user_id):
    event = Event.query.get_or_404(event_id)

    try:
        user_id_int = int(user_id)
    except ValueError:
        return jsonify({"message": "ID utilisateur invalide."}), 400

    if event.organisateur_id != user_id_int:
        return jsonify({"message": "Non autorisé à modifier cet événement."}), 403

    try:
        # Utilisation de request.form pour les champs textuels et request.files pour l'image
        data = request.form.to_dict()
        files = request.files
        
        # Mise à jour des champs standards
        for key in ['titre', 'description', 'lieu']:
            if key in data:
                setattr(event, key, data[key])
        
        # Gestion spéciale pour le type
        if 'type' in data:
            normalized_type = normalize_event_type(data['type'])
            if normalized_type:
                setattr(event, 'type', normalized_type)

        # Gestion spéciale pour la catégorie
        if 'categorie_id' in data:
            try:
                event.categorie_id = int(data['categorie_id'])
            except ValueError:
                pass  # Garde l'ancienne valeur si conversion échoue

        # Conversion des types spéciaux
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
        
        # Gestion de l'image
        if 'image' in files:
            image = files['image']
            if image.filename != '':  # Vérifier qu'un fichier a été envoyé
                filename = secure_filename(image.filename)
                upload_folder = current_app.config.get('UPLOAD_FOLDER', 'static/uploads')
                os.makedirs(upload_folder, exist_ok=True)
                image_path = os.path.join(upload_folder, filename)
                image.save(image_path)
                event.image_url = f"/{image_path.replace(os.sep, '/')}"
        
        # Mise à jour du champ est_valide
        if 'est_valide' in data:
            est_valide_str = data['est_valide'].lower()
            event.est_valide = est_valide_str in ['true', '1', 'yes', 'vrai', 'oui']

        db.session.commit()
        return jsonify({
            "message": "Événement mis à jour avec succès.",
            "type": event.type,
            "est_valide": event.est_valide
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur mise à jour événement {event_id}: {str(e)}", exc_info=True)
        return jsonify({"message": f"Erreur lors de la mise à jour : {str(e)}"}), 500

# ✅ Supprimer un événement
def delete_event_service(event_id, user_id):
    event = Event.query.get_or_404(event_id)

    try:
        user_id_int = int(user_id)
    except ValueError:
        return jsonify({"message": "ID utilisateur invalide."}), 400

    if event.organisateur_id != user_id_int:
        return jsonify({"message": "Non autorisé à supprimer cet événement."}), 403

    try:
        db.session.delete(event)
        db.session.commit()
        return jsonify({"message": "Événement supprimé avec succès."}), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur suppression événement {event_id}: {str(e)}", exc_info=True)
        return jsonify({"message": f"Erreur lors de la suppression : {str(e)}"}), 500

# ✅ Valider un événement
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