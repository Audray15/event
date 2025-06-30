from app.extensions import db
from app.modules.registration.models import Registration

def create_registration(user_id, event_id):
    registration = Registration(user_id=user_id, event_id=event_id)
    db.session.add(registration)
    db.session.commit()
    return registration

def delete_registration(registration):
    db.session.delete(registration)
    db.session.commit()

def get_user_registrations(user_id):
    return Registration.query.filter_by(user_id=user_id).all()

def get_event_registrations(event_id):
    return Registration.query.filter_by(event_id=event_id).all()

def is_user_registered(user_id, event_id):
    return Registration.query.filter_by(user_id=user_id, event_id=event_id).first() is not None
