from flask import Blueprint

share_bp = Blueprint('share', __name__)

from app.blueprints.share import routes
