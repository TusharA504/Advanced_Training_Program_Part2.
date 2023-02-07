from http import HTTPStatus
from flask import jsonify, request, current_app
import json
from botocore.exceptions import ClientError
from .service import *
from ..constant import *
from ..settings import region_name
from ..utils import *

def describe_all_db_at(region):
    rds_client = create_client(RDS_RESOURCE,region)
    db_instances = rds_client.describe_db_instances()
    db_info_list = []
    for db in db_instances['DBInstances']:
        db_info = {
            'db_name':db_instances['DBInstanceIdentifier'],
            'engine':db_instances['Engine'],
            'status':db_instances['DBInstanceStatus']
        }
        db_info_list.append(db_info)
    return db_info_list

def add_db_changes():
    regions = get_regions_list()
    available_regions=[region['RegionName'] for region in regions['Regions'] if region['OptInStatus']!='not-opted-in']
    available_regions.sort()
    all_databases_aws = {'DB_Instances':[],'regions':[]}
    for region in available_regions:
        databases = describe_all_db_at(region)
        if databases:
            all_databases_aws['DB_Instances'].append({"region":region,"databases":databases})
            all_databases_aws['regions'].append(region)
    db_instances = DBInstances.query.filter().all()
    all_databases_db=[]
    for database in db_instances:
        db_instance = {
            'db_name':database.db_name,
            'engine':database.engine,
            'status':database.status,
        }


# def get_log_groups():
#     try:
#         current_app.logger.info(
#             f"Got Request For Get Log Groups: {request.json}")
#         # request object parameters
#         db_name = request.json.get("db_name")
#         region = request.json.get('region')

#         # Validating Inputs
#         current_app.logger.info("Validating Inputs...")
#         Validations.validate_input_log_groups(
#             region=region,
#             default_region=region_name,
#             db_name=db_name
#         )
#         current_app.logger.info("Input Validation Successful" + u'\u2705')

#         # creating a client
#         current_app.logger.info(f"Creating client: '{region}'")
#         client = create_client(LOGS_RESOURCE, region)

#         # describing the log groups
#         current_app.logger.info("Describing the log groups")
#         logGroups = describe_log_groups(client, db_name)

#         db_status = describe_db_instance(db_name,region)['DBInstances'][0]['DBInstanceStatus']


#         # inserting changes in database or logGroups if any 
#         current_app.logger.info("Checking for changes in logGroups or DataBase...")
#         insert_logGroup_or_db_changes_to_db(db_name,logGroups,region,db_status)

#         # Getting logGroups from DataBase
#         current_app.logger.info("Fetching log groups from the DataBase...")
#         log_groups = get_log_groups_of_db(db_name,region)

#         current_app.logger.info("Sending Response")
#         return SUCCESS_RESPONSE('Log_Groups',log_groups,HTTPStatus.OK)

#     except ValidationError as validaterror:
#         error = validaterror.response['Error']
#         status_code = validaterror.response['Status Code']
#         return ERROR_RESPONSE(ERROR=error, STATUSCODE=status_code,MSG=LOG_GROUP_NOT_FOUND)

#     except Exception as error:
#         current_app.logger.error(str(error))
#         error = str(error)
#         status_code = HTTPStatus.BAD_REQUEST
#         return ERROR_RESPONSE(ERROR=error, STATUSCODE=status_code,MSG=LOG_GROUP_NOT_FOUND)


# # function to Find the log streams and query count within given time window
# def get_query_count():
#     try:
#         # request object parameter
#         current_app.logger.info(
#             f"Got Request For Get Log Streams: {request.json}")
#         region = request.json.get('region')
#         db_name = request.json.get('db_name')
#         # filter_pattern = request.json.get('filterPattern')
#         start_time = request.json.get('start_time')
#         end_time = request.json.get('end_time')

#         # Validating Inputs
#         current_app.logger.info("Validating Inputs...")
#         Validations.validate_input_query_count(
#             db_name=db_name,
#             region=region,
#             default_region=region_name,
#             start_time=start_time,
#             end_time=end_time
#         )
#         current_app.logger.info("Input Validation Successful" + u'\u2705')

#         # Converting Start-End time to miliseconds
#         start_time_miliseconds = convert_to_miliseconds(start_time)
#         end_time_miliseconds = convert_to_miliseconds(end_time)
#         current_app.logger.info(start_time_miliseconds)

#         # Creating Client
#         current_app.logger.info(
#             f"Creating client for {LOGS_RESOURCE} resource ")
#         client = create_client(LOGS_RESOURCE, region)

#         # calling describe_log_groups method
#         current_app.logger.info("Calling describe_log_groups method")
#         logGroups = describe_log_groups(client, db_name)
#         db_status = describe_db_instance(db_name,region)['DBInstances'][0]['DBInstanceStatus']

#         # inserting changes in database or logGroups if any 
#         current_app.logger.info("Checking for changes in logGroups or DataBase...")
#         insert_logGroup_or_db_changes_to_db(db_name,logGroups,region,db_status)

#         queries_of_log_groups = {}
#         for group in logGroups:
#             # Calling describe_log_streams method
#             current_app.logger.info("Calling describe_log_streams method")
#             streams = client.describe_log_streams(
#                 logGroupName=group,
#             )

#             # Getting log group type
#             logGroupType = group.split('/')[-1]
#             filter_pattern = request.json.get('filterPattern') if logGroupType == 'general' else ''
#             logStreams = [stream["logStreamName"] for stream in streams["logStreams"]]

#             # inserting changes in logStreams if any 
#             current_app.logger.info("Checking for changes in logStreams...")
#             insert_logstream_changes_to_db(group,logStreams,region)

            
#             # Calling filter_log_events method
#             current_app.logger.info("Calling filter_log_events method")
#             response = client.filter_log_events(
#                 logGroupName=group,
#                 logStreamNames=logStreams,
#                 startTime=start_time_miliseconds,
#                 endTime=end_time_miliseconds,
#                 filterPattern=filter_pattern
#             )

#             # return jsonify(response)
#             # Accessing events
#             events = response['events']

#             # Counting queries
#             queryCount = find_query_count(logGroupType, events,region)
#             current_app.logger.info(f"Found Query count")
#             db_queries = f"{group.split('/')[-2]} ({group.split('/')[-1]})"

#             queries_of_log_groups[db_queries] = queryCount

#         QueriesCount = get_queries_between(start_time_miliseconds,end_time_miliseconds,db_name,region)

        
#         # Sending response
#         current_app.logger.info("Sending response")
#         return SUCCESS_RESPONSE('Queries',QueriesCount,HTTPStatus.OK)

#     # exception handeling
#     except ValidationError as validaterror:
#         error = validaterror.response['Error']
#         status_code = validaterror.response['Status Code']
#         return ERROR_RESPONSE(ERROR=error, STATUSCODE=status_code,MSG=QUERIES_NOT_FOUND)

#     except Exception as error:
#         current_app.logger.error(str(error))
#         error = str(error)
#         status_code = HTTPStatus.BAD_REQUEST
#         return ERROR_RESPONSE(ERROR=error, STATUSCODE=status_code,MSG=QUERIES_NOT_FOUND)