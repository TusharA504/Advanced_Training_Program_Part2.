from http import HTTPStatus
from flask import jsonify, request, current_app
import json
from botocore.exceptions import ClientError
from .service import *
from ..constant import *
from ..settings import region_name
from ..utils import *


def get_region_list():
    regions = get_regions_list()
    available_regions=[]
    unavailable_regions=[]
    current_app.logger.info(f"Sorting available & unavailable regions")
    for region in regions['Regions']:
        if region['OptInStatus']=='not-opted-in':
            unavailable_regions.append(region['RegionName'])
        else:
            available_regions.append(region['RegionName'])
    current_app.logger.info(f"Removing us-east-1")
    available_regions.remove('us-east-1') if 'us-east-1' in available_regions else available_regions
    unavailable_regions.remove('us-east-1') if 'us-east-1' in unavailable_regions else unavailable_regions
    current_app.logger.info(f"Sorting lists")
    available_regions.sort()
    unavailable_regions.sort()
    available_regions.insert(0,'us-east-1')
    current_app.logger.info(f"Returing op")

    return jsonify({'available_regions':available_regions,'unavailable_regions':unavailable_regions})


# Gets the List of Databases for particular region
def get_db_list():
    try:
        region = request.json.get("region")
        current_app.logger.info(f"Got Request For DBInstances from '{region}' region")
        current_app.logger.info("Validating Inputs...")
        Validations.validate_region(region,region_name,EC2_RESOURCE)
        current_app.logger.info("Input Validation Successful" + u'\u2705')
        current_app.logger.info("Getting DBInstances info from AWS...")
        aws_databases_info = describe_all_awsdb_at(region)
        current_app.logger.info("Getting DBInstances info from Local Database...")
        local_databases_info = describe_all_localdb_at(region)
        add_live_changes_to_db(aws_databases_info,local_databases_info,region)        
        local_db_info = list(describe_all_localdb_at(region).values())
        return SUCCESS_RESPONSE("Databases",local_db_info,HTTPStatus.OK)

    except ValidationError as validaterror:
        error = validaterror.response['Error']
        current_app.logger.error(error)
        status_code = validaterror.response['Status Code']
        return ERROR_RESPONSE(ERROR=error, STATUSCODE=status_code,MSG=LOG_GROUP_NOT_FOUND)

    except Exception as error:
        error = str(error)
        current_app.logger.error(error)
        status_code = HTTPStatus.BAD_REQUEST
        return ERROR_RESPONSE(ERROR=error, STATUSCODE=status_code,MSG=LOG_GROUP_NOT_FOUND)


def get_log_group_list():
    try:
        current_app.logger.info(f"Got Request For Get Log Groups: {request.json}")
        # request object parameters
        db_name = request.json.get("db_name")
        region = request.json.get('region')
        current_app.logger.info("Validating Inputs...")
        Validations.validate_input_log_groups(region,region_name,db_name)
        current_app.logger.info("Input Validation Successful" + u'\u2705')
        current_app.logger.info("Getting Log Groups info from AWS...")
        DB_Instances = list(describe_all_localdb_at(region).keys()) if db_name=="" else [db_name]
        local_lg_list = []
        for db_instance in DB_Instances:
            aws_loggroups_info = describe_all_aws_loggroups_at(region,db_instance)
            local_loggroups_info = describe_all_local_loggroups_at(region,db_instance)
            aws_loggroups = aws_loggroups_info[db_instance]['lg_name']
            local_loggroups = local_loggroups_info[db_instance]['lg_name']
            new_loggroups = list(set(aws_loggroups).difference(local_loggroups))
            deleted_loggroups = list(set(local_loggroups).difference(aws_loggroups))
            db_id = get_db_id(db_instance,region)
            if new_loggroups:
                for new_loggroup in new_loggroups:
                    addLG(db_id,region,new_loggroup )
            if deleted_loggroups:
                for deleted_loggroup in deleted_loggroups:
                    deleteLG(db_id,region,deleted_loggroup)

            local_lg_info = describe_all_local_loggroups_at(region,db_instance)
            local_lg_list.append(local_lg_info[db_instance])
        return SUCCESS_RESPONSE("LogGroups",local_lg_list,HTTPStatus.OK)
    
    except ValidationError as validaterror:
        error = validaterror.response['Error']
        current_app.logger.error(error)
        status_code = validaterror.response['Status Code']
        return ERROR_RESPONSE(ERROR=error, STATUSCODE=status_code,MSG=LOG_GROUP_NOT_FOUND)

    except Exception as error:
        error = str(error)
        current_app.logger.error(error)
        status_code = HTTPStatus.BAD_REQUEST
        return ERROR_RESPONSE(ERROR=error, STATUSCODE=status_code,MSG=LOG_GROUP_NOT_FOUND)


def get_log_stream_list():
    try:
        current_app.logger.info(f"Got Request For Get Log Streams: {request.json}")
        region = request.json.get('region')
        db_name = request.json.get("db_name")
        current_app.logger.info("Validating Inputs...")
        Validations.validate_input_log_groups(region,region_name,db_name)
        current_app.logger.info("Input Validation Successful" + u'\u2705')
        current_app.logger.info("Getting Log Groups list from AWS...")
        Log_Groups = (describe_all_local_loggroups_at(region,db_name))[db_name]['lg_name']
        current_app.logger.info("Getting Log Groups list from AWS...")
        local_ls_list = []

        for Log_Group in Log_Groups:
            log_group = Log_Group.split('/')[-1]
            aws_log_streams = describe_all_aws_logstreams_at(region,log_group,db_name)
            local_log_streams = describe_all_local_logstreams_at(region,log_group,db_name)
            aws_logstreams = aws_log_streams[log_group]['ls_name']
            local_logstreams = local_log_streams[log_group]['ls_name']
            new_logstreams = list(set(aws_logstreams).difference(local_logstreams))
            deleted_logstreams = list(set(local_logstreams).difference(aws_logstreams))
            lg_id = get_logGroup_id(Log_Group,region)
            if new_logstreams:
                for new_logstreams in new_logstreams:
                    addLS(lg_id,region,new_logstreams)
            if deleted_logstreams:
                for deleted_logstream in deleted_logstreams:
                    deleteLS(lg_id,region,deleted_logstream)

            local_ls_info = describe_all_local_logstreams_at(region,log_group,db_name)
            local_ls_list.append(local_ls_info[log_group])
        return SUCCESS_RESPONSE("LogStreams",local_ls_list,HTTPStatus.OK)
    
    except ValidationError as validaterror:
        error = validaterror.response['Error']
        current_app.logger.error(error)
        status_code = validaterror.response['Status Code']
        return ERROR_RESPONSE(ERROR=f"Validationerror: {error}", STATUSCODE=status_code,MSG=LOG_GROUP_NOT_FOUND)

    except Exception as error:
        error = str(error)
        current_app.logger.error(f"Exception: {error}")
        status_code = HTTPStatus.BAD_REQUEST
        return ERROR_RESPONSE(ERROR=error, STATUSCODE=status_code,MSG=LOG_GROUP_NOT_FOUND)


def get_query_count():
    try:
        current_app.logger.info(f"Got Request For Query Count: {request.json}")
        region = request.json.get('region')
        db_name = request.json.get("db_name")
        start_time = request.json.get('start_time')
        end_time = request.json.get('end_time')
        # Validating Inputs
        current_app.logger.info("Validating Inputs...")
        Validations.validate_input_query_count(
            db_name=db_name,
            region=region,
            default_region=region_name,
            start_time=start_time,
            end_time=end_time
        )
        current_app.logger.info("Input Validation Successful" + u'\u2705')

        db_id = get_db_id(db_name,region)
        current_app.logger.info("Creating client in desc func")

        aws_query_events = describe_all_aws_querylogs_between(start_time,end_time,db_name,region)

        queries = {"TOTAL_QUERIES":0}
        events_list = []
        current_app.logger.info("for event in aws_query_events['events']")
        for event in aws_query_events['events']:
            message = event['message']
            time = event['timestamp']
            current_app.logger.info("Query Word NF")

            Query_word = extract_query_word(message)
            current_app.logger.info("Query Word NF")
            if Query_word:
                if not queryExists(time,db_id,Query_word.upper(),region):
                    addQuery(time,db_id,Query_word.upper(),region)
                
        local_query_events = describe_all_local_querylogs_between(start_time,end_time,db_name,region)
        for queryWord in local_query_events:
            if queryWord.upper() in queries.keys():
                queries[queryWord.upper()] += 1
                queries['TOTAL_QUERIES'] += 1
            else:
                queries[queryWord.upper()] = 1
                queries['TOTAL_QUERIES'] += 1
        
        queries_keys = list(queries.keys())
        queries_keys.remove('TOTAL_QUERIES')
        queries_list = [{'query':query,'count':queries[query]} for query in queries_keys]

        return jsonify({'Queries':queries_list,'TotalCount':queries['TOTAL_QUERIES']})
        


    except ValidationError as validaterror:
        error = validaterror.response['Error']
        current_app.logger.error(error)
        status_code = validaterror.response['Status Code']
        return ERROR_RESPONSE(ERROR=f"Validationerror: {error}", STATUSCODE=status_code,MSG=LOG_GROUP_NOT_FOUND)

    except Exception as error:
        error = str(error)
        current_app.logger.error(f"Exception: {error}")
        status_code = HTTPStatus.BAD_REQUEST
        return ERROR_RESPONSE(ERROR=error, STATUSCODE=status_code,MSG=LOG_GROUP_NOT_FOUND)
