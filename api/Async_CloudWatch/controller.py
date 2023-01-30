from http import HTTPStatus
from flask import jsonify, request, current_app
import json
from botocore.exceptions import ClientError
from .service import *
from .constant import *
from ..settings import region_name


def get_log_groups_async():
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
        current_app.logger.info("Input Validation Successful"+ u'\u2705')

        # sending message
        current_app.logger.info("Sending Message")
        response=send_message_to_trigger_lambda(region, request.json,GET_LOG_GROUPS)
        
        # Sending Response
        current_app.logger.info("Sending Response")
        return response

    except ValidationError as validaterror:
        error = validaterror.response['Error']
        status_code = validaterror.response['Status Code']
        return ERROR_RESPONSE(ERROR=error, STATUSCODE=status_code)

    except Exception as error:
        current_app.logger.error(str(error))
        error = str(error)
        status_code = HTTPStatus.BAD_REQUEST
        return ERROR_RESPONSE(ERROR=error, STATUSCODE=status_code)


# function to Find the log streams and query count within given time window
def get_query_count_async():
    try:
        # request object parameter
        current_app.logger.info(f"Got Request For Get Log Streams: {request.json}")
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
        current_app.logger.info("Input Validation Successful"+ u'\u2705')

        # Converting Start-End time to miliseconds
        start_time_miliseconds = convert_to_miliseconds(start_time)
        end_time_miliseconds = convert_to_miliseconds(end_time)

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

            # Getting log group type
            logGroupType = group.split('/')[-1]
            filter_pattern = request.json.get('filterPattern') if logGroupType=='general' else ''

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

            # Counting queries
            queryCount = find_query_count(logGroupType, events)
            db_queries = f"{group.split('/')[-2]} ({group.split('/')[-1]})"

            quries_of_log_groups[db_queries] = queryCount

        # Sending response
        current_app.logger.info("Sending response")
        return jsonify(quries_of_log_groups)


    # exception handeling
    except ValidationError as validaterror:
        error = validaterror.response['Error']
        status_code = validaterror.response['Status Code']
        return ERROR_RESPONSE(ERROR=error, STATUSCODE=status_code)


    except Exception as e:
        current_app.logger.error(str(e))
        return {"Error": str(e)}
