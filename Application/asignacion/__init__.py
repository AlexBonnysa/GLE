from flask import Blueprint
asignacion = Blueprint('asignacion_general', __name__, template_folder='templates', static_folder='static')
from . import routes
from . import Actualizar_pedidos