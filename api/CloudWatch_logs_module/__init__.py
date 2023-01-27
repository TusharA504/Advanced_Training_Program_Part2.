from flask import Blueprint
from .controller import *


# creates a blueprint for rds instance
cloudwatch_log_bp = Blueprint('rds', __name__, url_prefix='/api/cloudwatch/log')


# for get log-groups of rds instance
cloudwatch_log_bp.add_url_rule('/groups', 'get_log_groups', get_log_groups, methods=['GET'])

# for get log-streams
cloudwatch_log_bp.add_url_rule('/queries','get_log_streams',get_log_streams,methods=['GET'])


