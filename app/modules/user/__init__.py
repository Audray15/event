from flask import Blueprint

user_bp = Blueprint('user_bp', __name__, url_prefix='/api/users')

def register_user_routes(app):
    from .routes import user_bp as routes_bp
    app.register_blueprint(routes_bp)
