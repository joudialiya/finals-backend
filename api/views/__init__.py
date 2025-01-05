from flask import Blueprint

main_views = Blueprint('main_views', __name__, url_prefix='/api')

from api.views.auth import *
from api.views.core import *

