import os
from flask import Flask
from dotenv import load_dotenv

from app.extensions import db, migrate, jwt, cors, mail

# Charger les variables d'environnement depuis .env
load_dotenv()

# Importer les modèles pour que Flask-Migrate les reconnaisse
from app.modules.user.models import User
from app.modules.category.models import Category
from app.modules.event.models import Event
from app.modules.registration.models import Registration

def str_to_bool(value):
    return str(value).strip().lower() in ['true', '1', 't', 'yes']

def create_app():
    app = Flask(__name__)

    # === CONFIGURATION FLASK ===
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default_secret_key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI', 'sqlite:///default.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'default_jwt_secret')

    # === CONFIGURATION MAIL ===
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'localhost')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 25))
    app.config['MAIL_USE_TLS'] = str_to_bool(os.getenv('MAIL_USE_TLS', 'False'))
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

    # === INITIALISATION DES EXTENSIONS ===
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app)
    mail.init_app(app)

    # === ENREGISTREMENT DES BLUEPRINTS ===
    from app.modules.user.routes import user_bp
    from app.modules.auth import auth_bp
    from app.modules.category.routes import category_bp
    from app.modules.event.routes import event_bp
    from app.modules.registration.routes import registration_bp
    from app.modules.dashboard.routes import dashboard_bp

    app.register_blueprint(user_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(category_bp)
    app.register_blueprint(event_bp)
    app.register_blueprint(registration_bp, url_prefix='/api/registrations')
    app.register_blueprint(dashboard_bp)

    return app
