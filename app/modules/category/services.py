from app.extensions import db
from .models import Category
from sqlalchemy.exc import IntegrityError

def get_all_categories():
    return Category.query.all()

def get_category_by_id(category_id):
    return Category.query.get(category_id)

def create_category(nom, description=None):
    if Category.query.filter_by(nom=nom).first():
        return None

    category = Category(nom=nom, description=description)
    try:
        db.session.add(category)
        db.session.commit()
        return category
    except IntegrityError:
        db.session.rollback()
        return None

def update_category(category_id, nom=None, description=None):
    category = get_category_by_id(category_id)
    if not category:
        return None

    if nom:
        existing = Category.query.filter_by(nom=nom).first()
        if existing and existing.id != category.id:
            return None
        category.nom = nom

    if description is not None:
        category.description = description

    try:
        db.session.commit()
        return category
    except IntegrityError:
        db.session.rollback()
        return None

def delete_category(category_id):
    category = get_category_by_id(category_id)
    if not category:
        return False

    try:
        db.session.delete(category)
        db.session.commit()
        return True
    except Exception:
        db.session.rollback()
        return False