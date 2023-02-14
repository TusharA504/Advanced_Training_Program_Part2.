from flask import Blueprint
from .controller import *


# creates a blueprint for rds instance
cloudwatch_log_bp = Blueprint(
    'rds', __name__, url_prefix='/api/cloudwatch/log')


cloudwatch_log_bp.add_url_rule('/allregions', 'get_region_list', get_region_list, methods=['GET'])

cloudwatch_log_bp.add_url_rule('/alldb', 'get_db_list', get_db_list, methods=['POST'])

cloudwatch_log_bp.add_url_rule('/allgroups', 'get_log_group_list', get_log_group_list, methods=['POST'])

cloudwatch_log_bp.add_url_rule('/allstreams', 'get_log_stream_list', get_log_stream_list, methods=['POST'])

cloudwatch_log_bp.add_url_rule('/querycount', 'get_query_count', get_query_count, methods=['POST'])


