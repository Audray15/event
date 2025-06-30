import sys
from app import create_app
from app.extensions import db  # ✅ Assure-toi que db est bien importé depuis app/extensions.py
from app.modules.user.models import User  # ✅ Ajuste le chemin selon ton arborescence réelle

def create_superadmin(email="superadmin@example.com", password="SuperAdmin1234", name="SuperAdmin", telephone="657687447"):
    app = create_app()
    with app.app_context():
        existing_superadmin = User.query.filter_by(role='superadmin').first()
        if existing_superadmin:
            print(f"⚠️ Un superadmin existe déjà avec l'email: {existing_superadmin.email}")
            return

        superadmin = User(
            nom=name,
            email=email,
            telephone=telephone,
            role="superadmin",
            is_active=True
        )
        superadmin.set_password(password)
        db.session.add(superadmin)
        db.session.commit()
        print(f"✅ SuperAdmin créé avec succès ! Email: {email}, Mot de passe: {password}")

if __name__ == "__main__":  # ✅ CORRECTION ici
    email = "superadmin@example.com"
    password = "SuperAdmin1234"
    name = "SuperAdmin"
    telephone = "657687447"

    if len(sys.argv) > 1:
        email = sys.argv[1]
    if len(sys.argv) > 2:
        password = sys.argv[2]
    if len(sys.argv) > 3:
        name = sys.argv[3]
    if len(sys.argv) > 4:
        telephone = sys.argv[4]

    create_superadmin(email, password, name, telephone)
