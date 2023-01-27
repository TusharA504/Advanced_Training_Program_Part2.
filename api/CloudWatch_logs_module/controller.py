from http import HTTPStatus
from flask import jsonify, request, current_app
import json
from botocore.exceptions import ClientError
from .service import *
from .constant import *
from ..settings import region_name


def get_log_groups():
    try:
        current_app.logger.info(f"Got Request For Get Log Groups: {request.json}")
        # request object parameters
        db_name = request.json.get("db_name")
        region = request.json.get('region')
        
        # validation for region
        current_app.logger.info(f"Validating Region: '{region}'")
        Validations.validate_region(region,region_name,EC2_RESOURCE)
       
     
        # validation for db_name
        current_app.logger.info(f"Validating Database Name: '{db_name}'")
        Validations.validate_db_name(RDS_RESOURCE,db_name, region)

        # creating a client
        current_app.logger.info(f"Creating client: '{region}'")
        client = create_client(LOGS_RESOURCE, region)

        # describing the log groups
        current_app.logger.info("Describing the log groups")
        logGroups = describe_log_groups(client, db_name)

        # paginator = client.get_paginator('describe_log_groups')

        # response_iterator = paginator.paginate(
        #     logGroupNamePrefix=f'/aws/rds/instance/{db_name}',
        #     PaginationConfig={
        #         'MaxItems': 1,
        #         'PageSize': 5,
        #         'StartingToken': response["nextToken"]
        #     }
        # )

        # arr=[]
        # for groups in response_iterator:
        #     arr.append(groups)

        # sending response
        current_app.logger.info("Sending Response")
        return jsonify({"logGroups": logGroups}), HTTPStatus.OK

    # exception handeling
    except ClientError as e:
        current_app.logger.error(e.response['Error'])
        return {"error": e.response['Error']}, e.response['ResponseMetadata']['HTTPStatusCode']

    except Exception as e:
        
        current_app.logger.error(str(e))
        return {"Error": str(e)}, HTTPStatus.BAD_REQUEST


# function to Find the log streams within given time window
def get_log_streams():
    try:
        # request object parameter
        current_app.logger.info(f"Got Request For Get Log Streams: {request.json}")
        region = request.json.get('region')
        db_name = request.json.get('db_name')
        filter_pattern = request.json.get('filterPattern')
        start_time = request.json.get('start_time')
        end_time = request.json.get('end_time')
        start_time_miliseconds = convert_to_miliseconds(start_time)
        end_time_miliseconds = convert_to_miliseconds(end_time)

        # validation for region
        current_app.logger.info(f"Validating Region: '{region}'")
        Validations.validate_region(region, region_name, EC2_RESOURCE)
        
        # validation for db name
        current_app.logger.info(f"Validating Database Name: '{db_name}'")
        Validations.validate_db_name(RDS_RESOURCE, db_name, region)
        
        # time validation
        current_app.logger.info(f"Validating time: '{start_time,end_time}'")
        if end_time < start_time:
            raise Exception("end time must be greater than start time")
        
        current_app.logger.info(f"Validated time: '{start_time,end_time}'")

        # Creating Client
        current_app.logger.info(f"Creating client for {LOGS_RESOURCE} resource ")
        client = create_client(LOGS_RESOURCE, region)
      
        # calling describe_log_groups method
        current_app.logger.info("Calling describe_log_groups method")
        logGroups = describe_log_groups(client, db_name)

        quries_of_log_groups = {}
        for group in logGroups:
            # Calling describe_log_streams method
            current_app.logger.info("Calling describe_log_streams method")
            streams = client.describe_log_streams(
                logGroupName=group,

            )

            # Calling filter_log_events method
            current_app.logger.info("Calling filter_log_events method")
            response = client.filter_log_events(
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
