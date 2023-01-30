from http import HTTPStatus
from flask import jsonify, request, current_app
import json
from botocore.exceptions import ClientError
from .service import *
from .constant import *
from ..settings import region_name
from ..utils import ERROR_RESPONSE, SUCCESS_RESPONSE


def get_log_groups():
    try:
        current_app.logger.info(
            f"Got Request For Get Log Groups: {request.json}")
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
        current_app.logger.info(f"Creating client: '{region}'")
        client = create_client(LOGS_RESOURCE, region)

        # describing the log groups
        current_app.logger.info("Describing the log groups")
        logGroups = describe_log_groups(client, db_name)

        current_app.logger.info("Sending Response")
        return SUCCESS_RESPONSE(logGroups,HTTPStatus.OK)

    except ValidationError as validaterror:
        error = validaterror.response['Error']
        status_code = validaterror.response['Status Code']
        return ERROR_RESPONSE(ERROR=error, STATUSCODE=status_code,MSG=LOG_GROUP_NOT_FOUND)

    except Exception as error:
        current_app.logger.error(str(error))
        error = str(error)
        status_code = HTTPStatus.BAD_REQUEST
        return ERROR_RESPONSE(ERROR=error, STATUSCODE=status_code,MSG=LOG_GROUP_NOT_FOUND)


# function to Find the log streams and query count within given time window
def get_query_count():
    try:
        # request object parameter
        current_app.logger.info(
            f"Got Request For Get Log Streams: {request.json}")
        region = request.json.get('region')
        db_name = request.json.get('db_name')
        # filter_pattern = request.json.get('filterPattern')
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
        current_app.logger.info(
            f"Creating client for {LOGS_RESOURCE} resource ")
        client = create_client(LOGS_RESOURCE, region)

        # calling describe_log_groups method
        current_app.logger.info("Calling describe_log_groups method")
        logGroups = describe_log_groups(client, db_name)

        queries_of_log_groups = {}
        for group in logGroups:
            # Calling describe_log_streams method
            current_app.logger.info("Calling describe_log_streams method")
            streams = client.describe_log_streams(
                logGroupName=group,
            )

            # Getting log group type
            logGroupType = group.split('/')[-1]
            filter_pattern = request.json.get(
                'filterPattern') if logGroupType == 'general' else ''

            # Calling filter_log_events method
            current_app.logger.info("Calling filter_log_events method")
            response = client.filter_log_events(
                logGroupName=group,
                logStreamNames=[stream["logStreamName"]
                                for stream in streams["logStreams"]],
                startTime=start_time_miliseconds,
                endTime=end_time_miliseconds,
                filterPattern=filter_pattern
            )

            # Accessing events
            events = response['events']

            # Counting queries
            queryCount = find_query_count(logGroupType, events)
            db_queries = f"{group.split('/')[-2]} ({group.split('/')[-1]})"

            queries_of_log_groups[db_queries] = queryCount

        # Sending response
        current_app.logger.info("Sending response")
        return SUCCESS_RESPONSE(queries_of_log_groups,HTTPStatus.OK)

    # exception handeling
    except ValidationError as validaterror:
        error = validaterror.response['Error']
        status_code = validaterror.response['Status Code']
        return ERROR_RESPONSE(ERROR=error, STATUSCODE=status_code,MSG=QUERIES_NOT_FOUND)

    except Exception as error:
        current_app.logger.error(str(error))
        error = str(error)
        status_code = HTTPStatus.BAD_REQUEST
        return ERROR_RESPONSE(ERROR=error, STATUSCODE=status_code,MSG=QUERIES_NOT_FOUND)
