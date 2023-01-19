from flask import jsonify, request, current_app
import boto3
import json
from ..settings import aws_secret_access_key, aws_access_key_id, region_name
from botocore.exceptions import ClientError, WaiterError
from http import HTTPStatus
import logging
from datetime import datetime
from .service import convert_to_miliseconds


def get_log_groups():

    try:
        request_obj=request.json
        # creating a client
        current_app.logger.info("Creating client")
        client = boto3.client('logs', aws_access_key_id=aws_access_key_id,
                              aws_secret_access_key=aws_secret_access_key,
                              region_name=request_obj["region_name"])
        
        # describing the log groups
        current_app.logger.info("Describing the log groups")
        response = client.describe_log_groups(
            logGroupNamePrefix=f'/aws/rds/instance/{request_obj["db_name"]}',
        )

        # sending response
        current_app.logger.info("Sending Response")
        return jsonify(response["logGroups"]), HTTPStatus.OK
    
    except KeyError as e:
        current_app.logger.error(str(e))
        return {"Error":str(e)},HTTPStatus.BAD_REQUEST
    
    except Exception as e:
        current_app.logger.error(str(e))
        return {"Error":str(e)}, HTTPStatus.BAD_REQUEST


def get_log_streams():
    try:
        current_app.logger.info("Creating client")
        client = boto3.client('logs', aws_access_key_id=aws_access_key_id,
                              aws_secret_access_key=aws_secret_access_key,
                              region_name=region_name)

      
        
            
       
        return 

    except Exception as e:
        return {"Error": str(e)}
