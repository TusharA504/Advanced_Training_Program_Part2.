from http import HTTPStatus
from flask import jsonify, request, current_app
import json
from botocore.exceptions import ClientError
from .service import *
from ..constant import *
from ..settings import region_name
from ..utils import *


def get_log_groups_async():
    try:
        request_body = request.json
        current_app.logger.info(f"Got Request For Get Log Groups: {request_body}")
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
        response=send_message_to_trigger_lambda(region, request_body, QUEUE_URL['Log_groups'])
        
        # Sending Response
        current_app.logger.info("Sending Response")
        if response:
            return SUCCESS_RESPONSE(MESSAGE_SENT, HTTPStatus.OK)
        raise Exception("Unexpected Error Occured")

    except ValidationError as validaterror:
        error = validaterror.response['Error']
        status_code = validaterror.response['Status Code']
        return ERROR_RESPONSE(ERROR=error, STATUSCODE=status_code,MSG=MESSAGE_NOT_SENT)

    except Exception as error:
        error = str(error)
        current_app.logger.error(error)
        status_code = HTTPStatus.BAD_REQUEST
        return ERROR_RESPONSE(ERROR=error, STATUSCODE=status_code,MSG=MESSAGE_NOT_SENT)


# function to Find the log streams and query count within given time window
def get_query_count_async():
    try:
        # request object parameter
        request_body = request.json
        current_app.logger.info(f"Got Request For Get Log Streams: {request_body}")
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
        request_body['start_time'] = convert_to_miliseconds(start_time)
        request_body['end_time'] = convert_to_miliseconds(end_time)

        # sending message
        current_app.logger.info("Sending Message")
        response=send_message_to_trigger_lambda(region, request_body, QUEUE_URL['Queries'])

        # Sending Response
        current_app.logger.info("Sending Response")
        if response:
            return SUCCESS_RESPONSE(MESSAGE_SENT, HTTPStatus.OK)
        raise Exception("Unexpected Error Occured")

    # exception handeling
    except ValidationError as validaterror:
        error = validaterror.response['Error']
        status_code = validaterror.response['Status Code']
        return ERROR_RESPONSE(ERROR=error, STATUSCODE=status_code,MSG=MESSAGE_NOT_SENT)


    except Exception as error:
        error = str(error)
        current_app.logger.error(error)
        status_code = HTTPStatus.BAD_REQUEST
        return ERROR_RESPONSE(ERROR=error, STATUSCODE=status_code, MSG=MESSAGE_NOT_SENT)
