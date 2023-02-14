from flask import Blueprint
from .controller import *


# creates a blueprint for rds instance
extras_bp = Blueprint('extras', __name__, url_prefix='/api/extras')


# gets list of all regions
extras_bp.add_url_rule('/regionslist', 'get_region_list', get_region_list, methods=['GET'])

# gets list of all databases
extras_bp.add_url_rule('/dblist','get_db_list',get_db_list,methods=['POST'])

extras_bp.add_url_rule('/getter','getter',getter,methods=['POST'])

