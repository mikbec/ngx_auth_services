from flask import Blueprint

bp = Blueprint('auth_saml', __name__)

from . import views
