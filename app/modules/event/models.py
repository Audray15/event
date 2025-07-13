from datetime import datetime
from app.extensions import db

class Event(db.Model):
    __tablename__ = 'events'

    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    date = db.Column(db.DateTime, nullable=False)
    lieu = db.Column(db.String(255), nullable=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    image_url = db.Column(db.String(255), nullable=True)
    type = db.Column(db.String(20), default='public')
    est_valide = db.Column(db.Boolean, default=False)

    categorie_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    organisateur_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # CORRECTION : Définition explicite des relations
    categorie = db.relationship('Category', backref='events', lazy='joined')
    organisateur = db.relationship('User', backref='organised_events', lazy='joined')