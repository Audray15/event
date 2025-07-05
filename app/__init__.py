import os
from flask import Flask, jsonify
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import logging
from datetime import datetime
from app import config
from flask_cors import CORS
from sqlalchemy.orm import scoped_session, sessionmaker, declarative_base

from .extensions import db, migrate, jwt, cors, mail

# Charger les variables d'environnement depuis .env
load_dotenv()

def str_to_bool(value):
    return str(value).strip().lower() in ['true', '1', 't', 'yes', 'y']

def create_app():
    app = Flask(__name__)
    
    app.config.from_object(config)

    # === CONFIGURATION FLASK ===
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default_secret_key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI', 'sqlite:///default.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'default_jwt_secret')
    app.config['UPLOAD_FOLDER'] = 'static/uploads'  # Ajouté pour les téléchargements

    CORS(app, origins="*")  # Enable CORS for all origins

    # Configuration du logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)
    logger.info("Initialisation de l'application Flask")

    # === CONFIGURATION MAIL ===
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'localhost')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 25))
    app.config['MAIL_USE_TLS'] = str_to_bool(os.getenv('MAIL_USE_TLS', 'False'))
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

    logger.debug("Configuration mail chargée: SERVER=%s, PORT=%s, USE_TLS=%s, USERNAME=%s", 
        app.config['MAIL_SERVER'], app.config['MAIL_PORT'], app.config['MAIL_USE_TLS'], app.config['MAIL_USERNAME'])

    # === INITIALISATION DES EXTENSIONS ===
    logger.info("Initialisation des extensions Flask")
    db.init_app(app)
    logger.debug("Extension SQLAlchemy initialisée")
    migrate.init_app(app, db)
    logger.debug("Extension Flask-Migrate initialisée")
    jwt.init_app(app)
    logger.debug("Extension Flask-JWT-Extended initialisée")
    cors.init_app(app)
    logger.debug("Extension Flask-CORS initialisée")
    mail.init_app(app)
    logger.debug("Extension Flask-Mail initialisée")
    
    # === CONFIGURATION DU MOTEUR DE BASE DE DONNÉES ===
    database_uri = app.config['SQLALCHEMY_DATABASE_URI']
    logger.info(f"Connexion à la base de données: {database_uri}")
    
    engine_options = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_size': 20,
        'max_overflow': 10,
        'echo': True
    }
    
    # Création du moteur principal
    try:
        primary_engine = create_engine(database_uri, **engine_options)
        logger.info("Moteur SQLAlchemy créé avec succès")
    except Exception as e:
        logger.error("Erreur lors de la création du moteur SQLAlchemy: %s", e)
        raise
    
    # Configuration de la session factory
    try:
        # SessionLocal = sessionmaker(
        #     autocommit=False,
        #     autoflush=False,
        #     bind=primary_engine
        # )
        SessionLocal = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=primary_engine))
        Base = declarative_base()
        Base.query = SessionLocal.query_property()
        logger.info("Session factory SQLAlchemy configurée")
    except Exception as e:
        logger.error("Erreur lors de la configuration de la session factory: %s", e)
        raise
    
    # Fonction pour obtenir une nouvelle session
    def get_new_session():
        logger.debug("Création d'une nouvelle session SQLAlchemy")
        return SessionLocal()
    
    # Stocker la fonction dans l'application
    app.get_new_session = get_new_session
    
    # Importer les modèles
    try:
        from app.modules.user.models import User
        from app.modules.category.models import Category
        from app.modules.event.models import Event
        from app.modules.registration.models import Registration

        # Create database tables
        with app.app_context():
            db.create_all()
        logger.info("Modèles importés avec succès")
    except Exception as e:
        logger.error("Erreur lors de l'importation des modèles: %s", e)
        raise

    # === ENREGISTREMENT DES BLUEPRINTS ===
    try:
        from app.modules.user.routes import user_bp
        from app.modules.auth import auth_bp
        from app.modules.category.routes import category_bp
        from app.modules.event.routes import event_bp
        from app.modules.registration.routes import registration_bp
        from app.modules.dashboard.routes import dashboard_bp

        app.register_blueprint(user_bp)
        logger.info("Blueprint user_bp enregistré")
        app.register_blueprint(auth_bp)
        logger.info("Blueprint auth_bp enregistré")
        app.register_blueprint(category_bp)
        logger.info("Blueprint category_bp enregistré")
        app.register_blueprint(event_bp)
        logger.info("Blueprint event_bp enregistré")
        app.register_blueprint(registration_bp, url_prefix='/api/registrations')
        logger.info("Blueprint registration_bp enregistré avec url_prefix /api/registrations")
        app.register_blueprint(dashboard_bp)
        logger.info("Blueprint dashboard_bp enregistré")
    except Exception as e:
        logger.error("Erreur lors de l'enregistrement des blueprints: %s", e)
        raise
    
    # === ROUTE DE SANTÉ ===
    @app.route('/health')
    def health_check():
        logger.debug("Appel de la route /health")
        try:
            db.session.execute('SELECT 1')
            logger.info("Vérification de la santé de la base de données réussie")
            return jsonify({
                'status': 'healthy',
                'database': 'connected',
                'timestamp': datetime.utcnow().isoformat()
            }), 200
        except Exception as e:
            logger.error("Erreur lors de la vérification de la santé: %s", e)
            return jsonify({
                'status': 'unhealthy',
                'error': str(e)
            }), 500

    logger.info("Application Flask initialisée avec succès")
    return app