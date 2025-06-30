from flask import Blueprint

registration_bp = Blueprint('registration', __name__, url_prefix='/api/registrations')

from . import routes
