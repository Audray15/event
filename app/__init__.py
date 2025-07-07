import os
from flask import Flask, jsonify
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import logging
from datetime import datetime

from app.extensions import db, migrate, jwt, cors, mail

# Charger les variables d'environnement
load_dotenv()

# Importer les modèles
from app.modules.user.models import User
from app.modules.category.models import Category
from app.modules.event.models import Event
from app.modules.registration.models import Registration

def str_to_bool(value):
    return str(value).strip().lower() in ['true', '1', 't', 'yes', 'y']

def create_app():
    app = Flask(__name__)

    # Configuration de base
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default_secret_key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI', 'sqlite:///default.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'default_jwt_secret')
    
    # Correction de la configuration du dossier d'uploads
    base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    app.config['UPLOAD_FOLDER'] = os.path.join(base_dir, 'app', 'static', 'uploads')
    
    # Augmenter la limite à 10MB
    app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB

    # Configuration email
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = str_to_bool(os.getenv('MAIL_USE_TLS', 'True'))
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', os.getenv('MAIL_USERNAME'))

    # Configuration logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[logging.StreamHandler()]
    )

    # Initialisation des extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app)
    mail.init_app(app)  # Doit être après la config

    # Configuration de la base de données
    engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
    SessionLocal = sessionmaker(bind=engine)
    app.db_session = SessionLocal

    # Créer le dossier d'uploads s'il n'existe pas
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
        app.logger.info(f"Created upload folder at: {app.config['UPLOAD_FOLDER']}")

    # Enregistrement des blueprints
    from app.modules.user.routes import user_bp
    from app.modules.auth import auth_bp
    from app.modules.category.routes import category_bp
    from app.modules.event.routes import event_bp
    from app.modules.registration.routes import registration_bp
    from app.modules.dashboard.routes import dashboard_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(category_bp)
    app.register_blueprint(event_bp)
    app.register_blueprint(registration_bp, url_prefix='/api/registrations')
    app.register_blueprint(dashboard_bp)

    # Route de santé
    @app.route('/health')
    def health_check():
        try:
            db.session.execute('SELECT 1')
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'upload_folder': app.config['UPLOAD_FOLDER']
            }), 200
        except Exception as e:
            return jsonify({
                'status': 'unhealthy',
                'error': str(e)
            }), 500

    return app