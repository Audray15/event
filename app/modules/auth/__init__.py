from flask import Blueprint

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

from . import routes  # ⬅️ Cela importe les routes dès que le blueprint est créé
