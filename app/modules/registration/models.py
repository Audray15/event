from app.extensions import db
from datetime import datetime

class Registration(db.Model):
    __tablename__ = 'registrations'  # double underscore ici

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="registrations")
    event = db.relationship("Event", backref="registrations")
