from http import HTTPStatus
from flask import jsonify, request, current_app
import json
from botocore.exceptions import ClientError
from .service import *
from ..constant import *
from ..settings import region_name
from ..utils import *
from ..extensions import db
from .rds_model import *
from datetime import datetime, timedelta

def get_all_regions_from_aws():
    try:
        current_app.logger.info(f"Got Request For Get All Regions")

        current_app.logger.info(f"Calling get_all_regions_method")

        # calling get_all_regions method from service.py
        response=get_all_regions()
        
        current_app.logger.info(f"Validating Response..")
        # sending response
        if response["ResponseMetadata"]["HTTPStatusCode"]==HTTPStatus.OK:
            current_app.logger.info("Response Validation Successful " + u'\u2705')
            return SUCCESS_RESPONSE("Regions", response["Regions"], HTTPStatus.OK)
        else:
            raise Exception("Unexpected Error Occured")
   
    except Exception as e:
        error = str(e)
        current_app.logger.error(error)
        status_code = HTTPStatus.BAD_REQUEST
        return ERROR_RESPONSE(error, status_code)


def get_all_databases_from_aws():
    try:
        current_app.logger.info( f"Got Request For Get all databases: {request.json}")

        # getting region from request obj
        region = request.json.get('region')
        
        # validating region
        Validations.validate_region(region, region_name, EC2_RESOURCE)
        
        # calling get all database method from service.py 
        response=get_all_databases(region)
        
        # sending response
        return SUCCESS_RESPONSE("DBInstances",[{"DBInstanceIdentifier":instance.DBName,"DBInstanceStatus":instance.Status} for instance in response],HTTPStatus.OK)
    
    # handeling validation errors
    except ValidationError as validaterror:
        error = validaterror.response['Error']
        status_code = validaterror.response['Status Code']

        current_app.logger.error(error)
        return ERROR_RESPONSE(error,status_code)
    
    # handeling exceptions
    except Exception as error:
        error=str(error)
        current_app.logger.error(error)
        status_code=HTTPStatus.BAD_REQUEST
        return ERROR_RESPONSE(error,status_code)


def get_log_groups():
    try:
        current_app.logger.info(f"Got Request For Get Log Groups: {request.json}")
        
        # request object parameters
        db_name = request.json.get("db_name")
        region = request.json.get('region')

        # Validating Inputs
        current_app.logger.info("Validating Inputs...")
        Validations.validate_input_log_groups(
            region=region,
            default_region=region_name,
            db_name=db_name
        )
        current_app.logger.info("Input Validation Successful" + u'\u2705')

        # creating a client
        current_app.logger.info(f"Creating Log resource client: '{region}'")
        client = create_client(LOGS_RESOURCE, region)

        # describing the log groups
        current_app.logger.info("Describing the log groups")
        logGroups_from_aws = describe_log_groups(client, db_name)

        # log response from database
        current_app.logger.info("Describing the log groups from database")
        log_response = db_logs_response_method(db_name, region, logGroups_from_aws)

        current_app.logger.info("Sending Response")
        return SUCCESS_RESPONSE("log_groups",log_response, HTTPStatus.OK)
    

    # validation exception
    except ValidationError as validaterror:
        error = validaterror.response['Error']
        status_code = validaterror.response['Status Code']
        
        current_app.logger.error(error)
        if error == INVALID_DBNAME.format(db_name=db_name):
          delete_database_if_not_present_at_aws(db_name, region)

        return ERROR_RESPONSE(ERROR=error, STATUSCODE=status_code)

    except Exception as error:
        current_app.logger.error(str(error))
        error = str(error)
        status_code = HTTPStatus.BAD_REQUEST
        return ERROR_RESPONSE(ERROR=error, STATUSCODE=status_code)


def get_log_streams():
    try:
        # request obj parameters
        region = request.json.get('region')
        db_name = request.json.get('db_name')
        client = create_client(LOGS_RESOURCE, region)
        
        # valiadation for region and db name
        Validations.validate_region(region, region_name, EC2_RESOURCE)
        Validations.validate_db_name(RDS_RESOURCE, db_name, region)
        
        # getting log groups from aws
        logGroups_from_aws = describe_log_groups(client, db_name)
        
        # getting and adding log groups from db
        log_response = db_logs_response_method(db_name, region, logGroups_from_aws)

        # getting and adding log streams from db
        log_streams_response=db_streams_response_method(client,region,logGroups_from_aws)
        
        # sending response
        return jsonify({"log_streams":log_streams_response,"log_groups":log_response})

    # validation exception
    except ValidationError as validaterror:
        error = validaterror.response['Error']
        status_code = validaterror.response['Status Code']
    
        if error == INVALID_DBNAME.format(db_name=db_name):
          delete_database_if_not_present_at_aws(db_name, region)

        return ERROR_RESPONSE(ERROR=error, STATUSCODE=status_code)
    
    except Exception as error:
        error = str(error)
        status_code = HTTPStatus.BAD_REQUEST
        return ERROR_RESPONSE(ERROR=error, STATUSCODE=status_code)




# function to Find the log streams and query count within given time window
def get_query_count():
    try:
        # request object parameter
        current_app.logger.info(f"Got Request For Get Log Streams: {request.json}")
        region = request.json.get('region')
        db_name = request.json.get('db_name')
       
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

        # Converting Start-End time to miliseconds
        start_time_miliseconds = convert_to_miliseconds(start_time)
        end_time_miliseconds = convert_to_miliseconds(end_time)
        
        # Creating Client
        current_app.logger.info(f"Creating client for {LOGS_RESOURCE} resource ")
        client = create_client(LOGS_RESOURCE, region)

        # calling describe_log_groups method
        current_app.logger.info("Calling describe_log_groups method")
        logGroups_from_aws = describe_log_groups(client, db_name)
        
       
        logGroup_from_db=db_logs_response_method(db_name, region, logGroups_from_aws)
        
        # getting and adding log streams from db
        log_streams_response = db_streams_response_method(client, region, logGroups_from_aws)
        
        
        logGroup_for_query_count = LogGroups.query.filter_by(LogGroupName=f"/aws/rds/instance/{db_name}/audit", Region=region).all()
         
        get_query_count_from_db=db_queries_response_method(client, logGroup_for_query_count, start_time_miliseconds, end_time_miliseconds,region) 
     
        current_app.logger.info("Sending response")
        return jsonify(get_query_count_from_db),HTTPStatus.OK

    # exception handeling
    except ValidationError as validaterror:
        error = validaterror.response['Error']
        status_code = validaterror.response['Status Code']
    
        if error == INVALID_DBNAME.format(db_name=db_name):
          delete_database_if_not_present_at_aws(db_name, region)

        return ERROR_RESPONSE(ERROR=error, STATUSCODE=status_code)
    
    except Exception as error:
        current_app.logger.error(str(error))
        error = str(error)
        status_code = HTTPStatus.BAD_REQUEST
        return ERROR_RESPONSE(ERROR=error, STATUSCODE=status_code)
