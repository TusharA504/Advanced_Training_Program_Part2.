from http import HTTPStatus
import boto3
from flask import jsonify, request, current_app
import boto3
import json
from ..settings import aws_secret_access_key, aws_access_key_id, region_name
from botocore.exceptions import ClientError, WaiterError
from http import HTTPStatus
import logging
from datetime import datetime
from .service import convert_to_miliseconds, find_query_count,describe_log_groups


def get_log_groups():
    try:

        # request object parameters
        db_name = request.json.get("db_name")
        region = request.json.get('region')
      

        # creating a client
        current_app.logger.info(f"Creating client: '{region}'")
        client = boto3.client('logs', aws_access_key_id=aws_access_key_id,
                              aws_secret_access_key=aws_secret_access_key,
                              region_name=region)

        # describing the log groups
        
        current_app.logger.info("Describing the log groups")
        logGroups=describe_log_groups(client, db_name)
        
        # response = client.describe_log_groups(
        #     logGroupNamePrefix=f'/aws/rds/instance/{db_name}'
          
        # )

       
        # paginator = client.get_paginator('describe_log_groups')

        # response_iterator = paginator.paginate(
        #     logGroupNamePrefix=f'/aws/rds/instance/{db_name}',
        #     PaginationConfig={
        #         'MaxItems': 1,
        #         'PageSize': 5,
        #         'StartingToken': response["nextToken"]
        #     }
        # )
        
     
        # logGroups = [logGroup['logGroupName'] for logGroup in response['logGroups']]
        
        # arr=[]
        # for groups in response_iterator:
        #     arr.append(groups)

        # sending response
        current_app.logger.info("Sending Response")
        return jsonify({"logGroups": logGroups}), HTTPStatus.OK
    
    # exception handeling
    except Exception as e:
        current_app.logger.error(str(e))
        return {"Error": str(e)}, HTTPStatus.BAD_REQUEST


# function to Find the log streams within given time window
def get_log_streams():
    try:
        # request object parameter
        region = request.json.get('region')
        db_name=request.json.get('db_name')
        filter_pattern = request.json.get('filterPattern')
        start_time = request.json.get('start_time')
        end_time = request.json.get('end_time')
        start_time_miliseconds = convert_to_miliseconds(start_time)
        end_time_miliseconds = convert_to_miliseconds(end_time)

        # time validation
        if end_time < start_time:
            raise Exception("end time must be greater than start time")

        # Creating Client
        current_app.logger.info("Creating client")
        client = boto3.client('logs', aws_access_key_id=aws_access_key_id,
                              aws_secret_access_key=aws_secret_access_key,
                              region_name=region)
        
        # calling describe_log_groups method
        current_app.logger.info("Calling describe_log_groups method")
        logGroups= describe_log_groups(client,db_name)

        quries_of_log_groups={}
        for group in logGroups:

            # Calling describe_log_streams method
            current_app.logger.info("Calling describe_log_streams method")
            streams = client.describe_log_streams(
                logGroupName=group,
                
            )
            
            # Calling filter_log_events method
            current_app.logger.info("Calling filter_log_events method")
            response= client.filter_log_events(
                logGroupName=group,
                logStreamNames=[stream["logStreamName"]for stream in streams["logStreams"]],
                startTime=start_time_miliseconds,
                endTime=end_time_miliseconds,
                filterPattern=filter_pattern
            )
            
            # Accessing events
            events = response['events']

            # Getting log group type
            logGroupType = group.split('/')[-1]
            
            # Counting queries
            queryCount = find_query_count(logGroupType, events)
            db_queries = f"{group.split('/')[-2]} ({group.split('/')[-1]})"
            
            quries_of_log_groups[db_queries] = queryCount

        # Sending response
        current_app.logger.info("Sending response")
        return jsonify(quries_of_log_groups)

        # calling filter log events method
        # current_app.logger.info("Calling filter_log_events method")
        # response = client.filter_log_events(
        #     logGroupName=logGroupName,
        #     startTime=start_time_miliseconds,
        #     endTime=end_time_miliseconds,
        #     filterPattern=filter_pattern
        # )
        
        # events = response['events']
        # logGroupType = logGroupName.split('/')[-1]
     
        # # counting quries
        # current_app.logger.info("Calling find_query_count method")
        # queryCount = find_query_count(logGroupType,events)

        # # sending response
        # return jsonify(response)
    
    # exception handeling
    except Exception as e:
        current_app.logger.error(str(e))
        return {"Error": str(e)}
