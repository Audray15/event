from functools import wraps
from flask_jwt_extended import get_jwt
from flask import jsonify

ROLES_MAPPING = {
    "user": ["user", "utilisateur"],
    "organizer": ["organizer", "organisateur"],
    "admin": ["admin"],
    "super_admin": ["super_admin"],
    "visitor": ["visitor", "visiteur"]
}

def role_required(allowed_roles):
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            claims = get_jwt()
            user_role = claims.get("role")
            
            # Vérifie si le rôle est dans les rôles autorisés
            for role_group in allowed_roles:
                # Vérifie si le groupe est dans le mapping
                if role_group in ROLES_MAPPING:
                    if user_role in ROLES_MAPPING[role_group]:
                        return fn(*args, **kwargs)
                # Permet aussi d'utiliser directement des rôles spécifiques
                elif user_role == role_group:
                    return fn(*args, **kwargs)
            
            return jsonify({
                "message": "Accès refusé : rôle insuffisant.",
                "required_roles": allowed_roles,
                "your_role": user_role
            }), 403
        return decorator
    return wrapper