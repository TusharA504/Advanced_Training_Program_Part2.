from flask import Blueprint
from .controller import *


# creates a blueprint for rds instance
async_cloudwatch_bp = Blueprint('rds', __name__, url_prefix='/api/async/cloudwatch/log')


# for get log-groups of rds instance
async_cloudwatch_bp.add_url_rule('/asyncgroups', 'get_log_groups_async', get_log_groups_async, methods=['GET'])

# for get log-streams
async_cloudwatch_bp.add_url_rule('/queries','get_query_count_async',get_query_count_async,methods=['GET'])