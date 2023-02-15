from flask import Blueprint
from .controller import *


# creates a blueprint for rds instance
cloudwatch_log_bp = Blueprint(
    'async_rds', __name__, url_prefix='/api/cloudwatch/log')


# for get log-groups of rds instance
cloudwatch_log_bp.add_url_rule(
    '/groups', 'get_log_groups', get_log_groups, methods=['GET','POST'])

# for get log-streams
cloudwatch_log_bp.add_url_rule(
    '/queries', 'get_query_count', get_query_count, methods=['GET','POST'])


# for get all regions
cloudwatch_log_bp.add_url_rule('/log_regions','get_all_regions',get_all_regions_from_aws,methods=['GET'])


# for get all databases
cloudwatch_log_bp.add_url_rule('/get_databases','get_databases',get_all_databases_from_aws,methods=['GET','POST'])

# for get all streams
cloudwatch_log_bp.add_url_rule('/log_streams','get_streams',get_log_streams,methods=['GET','POST'])