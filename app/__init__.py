import os
from flask import Flask, jsonify
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
import logging
from datetime import datetime
from app import config
from flask_cors import CORS
from sqlalchemy.orm import scoped_session, sessionmaker, declarative_base
from flask_mail import Message

from .extensions import db, migrate, jwt, cors, mail

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

    CORS(app, origins=["*"])  # Enable CORS for all origins

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
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
    
    # Configuration email
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = str_to_bool(os.getenv('MAIL_USE_TLS', 'True'))
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')
    
    # Dossier uploads
    base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    app.config['UPLOAD_FOLDER'] = os.path.join(base_dir, 'app', 'static', 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB

    # Logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[logging.StreamHandler()]
    )

    # Initialisation des extensions
    db.init_app(app)
    logger.debug("Extension SQLAlchemy initialisée")
    migrate.init_app(app, db)
    logger.debug("Extension Flask-Migrate initialisée")
    jwt.init_app(app)
    logger.debug("Extension Flask-JWT-Extended initialisée")
    cors.init_app(app)
    logger.debug("Extension Flask-CORS initialisée")
    mail.init_app(app)

    # Configuration de la session DB
    engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
    app.db_session = scoped_session(sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False
    ))

    # Créer le dossier d'uploads
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
        app.logger.info(f"Dossier upload créé : {app.config['UPLOAD_FOLDER']}")

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

    # Route de test email - Version corrigée et simplifiée
    @app.route('/test-email', methods=['GET'])
    def test_email():
        try:
            test_email = os.getenv('TEST_EMAIL', 'test@example.com')
            
            # Création du message avec les paramètres positionnels corrects
            msg = Message(
                "Test Email Service - API Événements",  # Sujet
                recipients=[test_email],  # Destinataires
                body="Ceci est un test du service email de l'API Événements."  # Corps
            )
            
            mail.send(msg)  # Envoi via l'extension mail
            
            app.logger.info(f"Email de test envoyé à {test_email}")
            return jsonify({
                "message": "Email de test envoyé avec succès",
                "recipient": test_email
            }), 200
        except Exception as e:
            app.logger.error(f"Erreur envoi email: {str(e)}")
            return jsonify({
                "error": str(e),
                "message": "Échec de l'envoi de l'email de test"
            }), 500

    # Route de santé
    @app.route('/health')
    def health_check():
        logger.debug("Appel de la route /health")
        try:
            # Vérification de la base de données
            db.session.execute('SELECT 1')
            
            # Vérification de la configuration email
            email_configured = bool(
                app.config['MAIL_USERNAME'] and 
                app.config['MAIL_PASSWORD'] and
                app.config['MAIL_SERVER']
            )
            
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'database': 'ok',
                'email_configured': email_configured,
                'mail_server': app.config['MAIL_SERVER']
            }), 200
        except Exception as e:
            logger.error("Erreur lors de la vérification de la santé: %s", e)
            return jsonify({
                'status': 'unhealthy',
                'error': str(e),
                'database': 'error'
            }), 500

    return app