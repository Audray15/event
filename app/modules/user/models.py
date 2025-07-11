from datetime import datetime, timedelta
from app.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
import random

class User(db.Model):
    __tablename__ = 'users'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    telephone = db.Column(db.String(20), nullable=True)

    role = db.Column(
        db.Enum('visitor', 'user', 'organizer', 'admin', 'super_admin', name='user_roles'),
        nullable=False,
        default='user'
    )

    is_active = db.Column(db.Boolean, default=True)
    reset_code = db.Column(db.String(6), nullable=True)
    reset_code_expiration = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, raw_password):
        self.password = generate_password_hash(raw_password, method='scrypt')

    def check_password(self, raw_password):
        return check_password_hash(self.password, raw_password)
    
    def generate_reset_code(self):
        self.reset_code = str(random.randint(100000, 999999))  # Code à 6 chiffres
        self.reset_code_expiration = datetime.utcnow() + timedelta(minutes=10)
        return self.reset_code
    
    def is_reset_code_valid(self, code):
        if not self.reset_code or not self.reset_code_expiration:
            return False
        return (self.reset_code == code and 
                datetime.utcnow() < self.reset_code_expiration)

    def to_dict(self):
        return {
            'id': self.id,
            'nom': self.nom,
            'email': self.email,
            'telephone': self.telephone,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }