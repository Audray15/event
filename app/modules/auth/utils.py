from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt, get_jwt_identity
from app.modules.user.models import User

jwt_blocklist = set()

def revoke_token(jti):
    jwt_blocklist.add(jti)

def is_token_revoked(jti):
    return jti in jwt_blocklist

def role_required(required_roles):
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            claims = get_jwt()
            role = claims.get("role")
            if role not in required_roles:
                return jsonify({"message": "Accès refusé : rôle non autorisé."}), 403
            return fn(*args, **kwargs)
        return decorator
    return wrapper

def is_admin():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    return user and user.role in ['admin', 'super_admin']
