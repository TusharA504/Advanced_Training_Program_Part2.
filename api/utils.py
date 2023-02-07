from flask import jsonify,current_app
import boto3
import re
from .settings import aws_secret_access_key, aws_access_key_id, region_name
from http import HTTPStatus
from datetime import datetime
from botocore.exceptions import ClientError
from .constant import *

def describe_db_instance(db_name,region):
    rds_client = create_client(RDS_RESOURCE,region)
    response = rds_client.describe_db_instances(DBInstanceIdentifier=db_name)
    return response

def create_client(resource, region):
    client = boto3.client(resource, aws_access_key_id=aws_access_key_id,
                          aws_secret_access_key=aws_secret_access_key,
                          region_name=region)
    return client

def get_regions_list():
    resource=EC2_RESOURCE
    default_region=region_name
    ec2_client = create_client(resource, default_region)
    response = ec2_client.describe_regions(AllRegions=True)
    return response



# Class that inherits Exception and has attribute as response
class ValidationError(Exception):
    def __init__(self, response):
        self.response = response

class DataBaseError(Exception):
    def __init__(self, response):
        self.response = response


class Validations():

    def validate_db_name(resource, db_name, region):
        current_app.logger.info(f"Validating Database Name: '{db_name}'...")
        # creating RDS Client
        client = create_client(resource, region)
        # calling describe_db_instances method
        try:
            response = client.describe_db_instances(DBInstanceIdentifier=db_name)
            current_app.logger.info("Database Name Validation Successful " + u'\u2705')

        except Exception as error:
            current_app.logger.error(error.response['Error']['Message'])
            error = INVALID_DBNAME.format(db_name=db_name)
            status_code = HTTPStatus.BAD_REQUEST
            raise ValidationError({"Error": error, "Status Code": status_code})

    def validate_region(region, default_region, resource):
        current_app.logger.info(f"Validating region: '{region}'...")

        regions_list = get_regions_list()

        # checks for valid enabled region
        is_region = False
        for reg in regions_list["Regions"]:
            if reg["RegionName"] == region:
                is_region = True
                if not (reg["OptInStatus"] == OPT_IN_NOT_REQUIRED or reg["OptInStatus"] == OPTED_IN):
                    error = f'Region {region} {reg["OptInStatus"]}'
                    status_code = HTTPStatus.BAD_REQUEST
                    raise ValidationError(
                        {"Error": error, "Status Code": status_code})

        if not is_region:
            error = INVALID_REGION
            status_code = HTTPStatus.BAD_REQUEST
            raise ValidationError({"Error": error, "Status Code": status_code})

        current_app.logger.info("Region Validation Successful " + u'\u2705')

    def validate_datetime(date_time):
        pattern = re.compile(DATE_TIME_FORMAT)
        date_time = date_time

        if not re.fullmatch(pattern, date_time):
            error = INVALID_DATETIME_FORMAT
            status_code = HTTPStatus.BAD_REQUEST
            current_app.logger.info(error)
            raise ValidationError({"Error": error, "Status Code": status_code})

    def validate_endtime(end_time):
        date_time_format = '%d/%m/%Y %H:%M:%S'
        current_time = datetime.now()
        end_time = datetime.strptime(end_time[:-5], date_time_format)
        if end_time > current_time:
            error = INVALID_ENDTIME.format(current_time=current_time)
            status_code = HTTPStatus.BAD_REQUEST
            current_app.logger.info(error)
            raise ValidationError({"Error": error, "Status Code": status_code})

    def validate_start_end_datetime(start_time, end_time):
        date_time_format = '%d/%m/%Y %H:%M:%S'
        start_time = datetime.strptime(start_time[:-5], date_time_format)
        end_time = datetime.strptime(end_time[:-5], date_time_format)
        if end_time < start_time:
            error = INVALID_DATE_TIME_WINDOW
            status_code = HTTPStatus.BAD_REQUEST
            current_app.logger.info(error)
            raise ValidationError({"Error": error, "Status Code": status_code})

    def validate_input_log_groups(region, default_region, db_name):
        Validations.validate_region(region, default_region, EC2_RESOURCE)
        Validations.validate_db_name(RDS_RESOURCE, db_name, region)

    def validate_input_query_count(db_name, region, default_region, start_time, end_time):
        Validations.validate_region(region, default_region, EC2_RESOURCE)
        Validations.validate_db_name(RDS_RESOURCE, db_name, region)
        current_app.logger.info("Validating start-end datetime...")
        Validations.validate_datetime(start_time)
        Validations.validate_datetime(end_time)
        Validations.validate_endtime(end_time)
        Validations.validate_start_end_datetime(start_time, end_time)
        current_app.logger.info("Datetime Validation Successful " + u'\u2705')


def ERROR_RESPONSE(ERROR, STATUSCODE, MSG):
    errorResponse = {"Error": ERROR, "Message": MSG}
    return jsonify(errorResponse), STATUSCODE


def SUCCESS_RESPONSE(CONTENT_NAME,CONTENT, STATUSCODE):
    successResponse = {CONTENT_NAME: CONTENT}
    return jsonify(successResponse), STATUSCODE
