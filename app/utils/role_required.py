from functools import wraps
from flask_jwt_extended import get_jwt
from flask import jsonify

ROLE_ALIASES = {
    "user": "utilisateur",
    "utilisateur": "utilisateur",
    "organizer": "organisateur",
    "organisateur": "organisateur",
    "admin": "admin",
    "super_admin": "super_admin",
    "visitor": "visiteur",
    "visiteur": "visiteur"
}

def role_required(allowed_roles):
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            claims = get_jwt()
            user_role = claims.get("role")
            normalized_role = ROLE_ALIASES.get(user_role, user_role)
            if normalized_role not in allowed_roles:
                return jsonify({"message": "Accès refusé : rôle insuffisant."}), 403
            return fn(*args, **kwargs)
        return decorator
    return wrapper
