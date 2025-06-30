from app.extensions import db
from app.modules.user.models import User
from app.modules.event.models import Event
from app.modules.registration.models import Registration

# 🟢 Dashboard global (admin, super_admin)
def get_global_stats():
    total_users = User.query.count()
    total_organizers = User.query.filter_by(role='organizer').count()

    total_events = Event.query.count()
    total_public_events = Event.query.filter_by(type='public').count()
    total_private_events = Event.query.filter_by(type='privé').count()

    total_validated_events = Event.query.filter_by(est_valide=True).count()
    total_pending_events = Event.query.filter_by(est_valide=False).count()

    total_registrations = Registration.query.count()

    return {
        "total_users": total_users,
        "total_organizers": total_organizers,
        "total_events": total_events,
        "total_public_events": total_public_events,
        "total_private_events": total_private_events,
        "total_validated_events": total_validated_events,
        "total_pending_events": total_pending_events,
        "total_registrations": total_registrations
    }

# 🟢 Dashboard perso organisateur
def get_organizer_stats(organizer_id):
    events = Event.query.filter_by(organisateur_id=organizer_id).all()
    total_events = len(events)
    total_validated_events = len([e for e in events if e.est_valide])
    total_pending_events = len([e for e in events if not e.est_valide])

    total_registrations = sum([len(e.registrations) for e in events])

    return {
        "total_events": total_events,
        "total_validated_events": total_validated_events,
        "total_pending_events": total_pending_events,
        "total_registrations": total_registrations
    }

# 🟢 "Dashboard" user = ses participations
def get_user_stats(user_id):
    registrations = Registration.query.filter_by(user_id=user_id).all()
    total_registrations = len(registrations)
    events = [r.event for r in registrations]

    events_info = [{
        "event_id": e.id,
        "titre": e.titre,
        "date": e.date.strftime('%Y-%m-%d'),
        "lieu": e.lieu
    } for e in events]

    return {
        "total_registrations": total_registrations,
        "events": events_info
    }
