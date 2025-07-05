from app.extensions import db
from app.modules.user.models import User
from app.modules.event.models import Event
from app.modules.registration.models import Registration

def get_global_stats():
    try:
        stats = {
            "total_users": User.query.count(),
            "total_organizers": User.query.filter(User.role.in_(['organizer', 'organisateur'])).count(),
            "total_events": Event.query.count(),
            "total_public_events": Event.query.filter_by(type='public').count(),
            "total_private_events": Event.query.filter_by(type='privé').count(),
            "total_validated_events": Event.query.filter_by(est_valide=True).count(),
            "total_pending_events": Event.query.filter_by(est_valide=False).count(),
            "total_registrations": Registration.query.count()
        }
        return stats
    except Exception as e:
        return {"error": str(e)}

def get_organizer_stats(organizer_id):
    try:
        events = Event.query.filter_by(organisateur_id=organizer_id).all()
        return {
            "total_events": len(events),
            "total_validated_events": len([e for e in events if e.est_valide]),
            "total_pending_events": len([e for e in events if not e.est_valide]),
            "total_registrations": sum(len(e.registrations) for e in events)
        }
    except Exception as e:
        return {"error": str(e)}

def get_user_stats(user_id):
    try:
        registrations = Registration.query.filter_by(user_id=user_id).all()
        return {
            "total_registrations": len(registrations),
            "events": [{
                "event_id": r.event.id,
                "titre": r.event.titre,
                "date": r.event.date.strftime('%Y-%m-%d'),
                "lieu": r.event.lieu
            } for r in registrations]
        }
    except Exception as e:
        return {"error": str(e)}