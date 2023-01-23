from http import HTTPStatus
import boto3
from flask import jsonify, request, current_app
from .service import convert_to_miliseconds, find_query_count
from ..settings import aws_secret_access_key, aws_access_key_id


def get_log_groups():
    try:
        db_name = request.json.get("db_name")
        region = request.json.get('region')

        # creating a client
        current_app.logger.info(f"Creating client: '{region}'")

        client = boto3.client('logs', aws_access_key_id=aws_access_key_id,
                              aws_secret_access_key=aws_secret_access_key,
                              region_name=region)

        # describing the log groups
        current_app.logger.info("Describing the log groups")
        response = client.describe_log_groups(
            logGroupNamePrefix=f'/aws/rds/instance/{db_name}',
        )

        log_groups = [logGroup['logGroupName'] for logGroup in response['logGroups']]

        # sending response
        current_app.logger.info("Sending Response")
        return jsonify({"logGroups": log_groups}), HTTPStatus.OK

    # exception handling
    except Exception as e:
        current_app.logger.error(str(e))
        return {"Error": str(e)}, HTTPStatus.BAD_REQUEST


# function to Find the log streams within given time window
def get_log_streams():
    try:
        # request object parameter
        region = request.json.get('region')
        log_group_name = request.json.get('logGroupName')
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

        # calling filter log events method
        current_app.logger.info("Calling filter_log_events method")
        response = client.filter_log_events(
            logGroupName=log_group_name,
            startTime=start_time_miliseconds,
            endTime=end_time_miliseconds,
            filterPattern=filter_pattern
        )

        events = response['events']
        log_group_type = log_group_name.split('/')[-1]

        # counting queries
        current_app.logger.info("Calling find_query_count method")
        query_count = find_query_count(log_group_type, events)

        # sending response
        return jsonify(query_count)

    # exception handling
    except Exception as e:
        current_app.logger.error(str(e))
        return {"Error": str(e)}
