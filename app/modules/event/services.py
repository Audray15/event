from flask import request, jsonify, current_app
from datetime import datetime
from app.extensions import db
from app.modules.event.models import Event
from werkzeug.utils import secure_filename
import os

# ✅ Créer un événement (image + données formulaire)
def create_event_service(request, user_id):
    try:
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
        latitude = float(request.form.get('latitude', 0))
        longitude = float(request.form.get('longitude', 0))
        type_evt = request.form.get('type', 'public')
        est_valide = request.form.get('est_valide', 'false').lower() in ['true', '1', 'yes']

        # Traitement de l'image
        image = request.files.get('image')
        image_url = None
        if image:
            filename = secure_filename(image.filename)
            upload_folder = current_app.config.get('UPLOAD_FOLDER', 'static/uploads')
            os.makedirs(upload_folder, exist_ok=True)
            image_path = os.path.join(upload_folder, filename)
            image.save(image_path)
            image_url = f"/{image_path.replace(os.sep, '/')}"

        event = Event(
            titre=titre,
            description=description,
            date=date,
            lieu=lieu,
            latitude=latitude,
            longitude=longitude,
            image_url=image_url,
            type=type_evt,
            est_valide=est_valide,
            categorie_id=int(categorie_id),
            organisateur_id=user_id
        )

        db.session.add(event)
        db.session.commit()

        return jsonify({"message": "Événement créé avec succès.", "event_id": event.id}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Erreur lors de la création : {str(e)}"}), 500

# ✅ Récupérer tous les événements (admin/organisateur)
def get_events_service(request):
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    type_filter = request.args.get('type')
    categorie_id = request.args.get('categorie_id')

    query = Event.query
    if type_filter:
        query = query.filter_by(type=type_filter)
    if categorie_id:
        query = query.filter_by(categorie_id=categorie_id)

    events = query.paginate(page=page, per_page=per_page, error_out=False)
    now = datetime.now()

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

# ✅ Récupérer les événements publics (visiteurs)
def get_public_events_service(request):
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))

    query = Event.query.filter_by(type='public', est_valide=True)
    events = query.paginate(page=page, per_page=per_page, error_out=False)
    now = datetime.now()

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

# ✅ Mettre à jour un événement (JSON uniquement)
def update_event_service(request, event_id, user_id):
    event = Event.query.get_or_404(event_id)

    if event.organisateur_id != user_id:
        return jsonify({"message": "Non autorisé à modifier cet événement."}), 403

    data = request.get_json()
    try:
        for key, value in data.items():
            if hasattr(event, key):
                if key == "date":
                    try:
                        setattr(event, key, datetime.fromisoformat(value))
                    except ValueError:
                        return jsonify({"message": "Format de date invalide pour mise à jour."}), 400
                else:
                    setattr(event, key, value)

        db.session.commit()
        return jsonify({"message": "Événement mis à jour avec succès."}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Erreur lors de la mise à jour : {str(e)}"}), 500

# ✅ Supprimer un événement
def delete_event_service(event_id, user_id):
    event = Event.query.get_or_404(event_id)

    if event.organisateur_id != user_id:
        return jsonify({"message": "Non autorisé à supprimer cet événement."}), 403

    try:
        db.session.delete(event)
        db.session.commit()
        return jsonify({"message": "Événement supprimé avec succès."}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Erreur lors de la suppression : {str(e)}"}), 500

# ✅ Valider un événement
def valider_event_service(event_id, user_id):
    event = Event.query.get_or_404(event_id)

    if event.organisateur_id != user_id:
        return jsonify({"message": "Non autorisé à valider cet événement."}), 403

    try:
        event.est_valide = True
        db.session.commit()
        return jsonify({"message": "Événement validé avec succès."}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Erreur lors de la validation : {str(e)}"}), 500
