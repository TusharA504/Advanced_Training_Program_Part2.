from datetime import datetime
import re
import boto3
from ..settings import aws_secret_access_key, aws_access_key_id,region_name
from http import HTTPStatus
from .constant import *
from botocore.exceptions import ClientError
from flask import current_app

# Class that inherits Exception and has attribute as response
class ValidationError(Exception):
    def __init__(self, response):
        self.response = response

def create_client(resource,region):
    client = boto3.client(resource, aws_access_key_id=aws_access_key_id,
                          aws_secret_access_key=aws_secret_access_key,
                          region_name=region)
    return client


def convert_to_miliseconds(time):
    end_time = time
    datetime_format = '%d/%m/%Y %H:%M:%S.%f'
    formatted_time = datetime.strptime(end_time, datetime_format)
    time_in_miliseconds = int(formatted_time.timestamp())*1000
    return time_in_miliseconds



def describe_log_groups(client,db_name):

    response = client.describe_log_groups(
        logGroupNamePrefix=f'/aws/rds/instance/{db_name}'

    )
    if not response['ResponseMetadata']['HTTPStatusCode']==HTTPStatus.OK:
        raise Exception("Unexpeted Error")
    
    logGroups = [logGroup['logGroupName']
                 for logGroup in response['logGroups']]
    
    return logGroups


def find_query_count(logGroupType,events):
    queries = {"TOTAL_QUERIES":0}
    for event in events:
        if logGroupType == "slowquery":
            new = event['message'].split('\n')[-1]
            query = new.split()[0]
            if query.upper() in queries.keys():
                queries[query.upper()] += 1
                queries['TOTAL_QUERIES'] += 1
            elif query.isalpha():
                queries[query.upper()] = 1
                queries['TOTAL_QUERIES'] += 1
            # return event['message']
        elif logGroupType == "general":
            new = event['message'].split()
            # query_index = new.index("Query") if "Query" in new else None
            query = new[3]
            # new[query_index+1]
            # if query_index else ""
            if query.upper() in queries.keys():
                queries[query.upper()] += 1
                queries['TOTAL_QUERIES'] += 1
            elif query.isalpha():
                queries[query.upper()] = 1
                queries['TOTAL_QUERIES'] += 1
            # return events 
 
    return queries
   
class Validations():

    def validate_db_name(resource,db_name,region):
        current_app.logger.info(f"Validating Database Name: '{db_name}'...")
        # creating RDS Client
        client=create_client(resource, region)
        # calling describe_db_instances method
        try:
            response = client.describe_db_instances(DBInstanceIdentifier=db_name)
            current_app.logger.info("Database Name Validation Successful "+ u'\u2705')

        except Exception as error:
            current_app.logger.error(error.response['Error']['Message'])
            error = INVALID_DBNAME.format(db_name=db_name)
            status_code = HTTPStatus.BAD_REQUEST
            raise ValidationError({"Error":error,"Status Code":status_code})
   
     

    def validate_region(region,default_region,resource):
        current_app.logger.info(f"Validating region: '{region}'...")
        # creating ec2 client
        ec2_client = create_client(resource, default_region)
        response = ec2_client.describe_regions(AllRegions=True)
        
        # checks for valid enabled region
        is_region=False
        for reg in response["Regions"]:
            if reg["RegionName"]==region:
                is_region=True
                if not (reg["OptInStatus"]==OPT_IN_NOT_REQUIRED or reg["OptInStatus"]==OPTED_IN):
                    error = f'Region {region} {reg["OptInStatus"]}'
                    status_code = HTTPStatus.BAD_REQUEST
                    raise ValidationError({"Error":error,"Status Code":status_code})
        
        if not is_region:
            error = INVALID_REGION
            status_code = HTTPStatus.BAD_REQUEST
            raise ValidationError({"Error":error,"Status Code":status_code})
        
        current_app.logger.info("Region Validation Successful "+ u'\u2705')


    def validate_datetime(date_time):
        pattern = re.compile(DATE_TIME_FORMAT)
        date_time = date_time

        if not re.fullmatch(pattern,date_time):
            error = INVALID_DATETIME_FORMAT
            status_code = HTTPStatus.BAD_REQUEST
            current_app.logger.info(error)
            raise ValidationError({"Error":error,"Status Code":status_code})
    
    def validate_endtime(end_time):
        date_time_format = '%d/%m/%Y %H:%M:%S'
        current_time = datetime.now()
        end_time = datetime.strptime(end_time[:-5], date_time_format)
        if end_time > current_time:
            error = INVALID_ENDTIME.format(current_time=current_time)
            status_code = HTTPStatus.BAD_REQUEST
            current_app.logger.info(error)
            raise ValidationError({"Error":error,"Status Code":status_code})
        
    def validate_start_end_datetime(start_time,end_time):
        date_time_format = '%d/%m/%Y %H:%M:%S'
        start_time = datetime.strptime(start_time[:-5], date_time_format)
        end_time = datetime.strptime(end_time[:-5], date_time_format)
        if end_time < start_time:
            error = INVALID_DATE_TIME_WINDOW
            status_code = HTTPStatus.BAD_REQUEST
            current_app.logger.info(error)
            raise ValidationError({"Error":error,"Status Code":status_code})

    def validate_input_log_groups(region,default_region,db_name):
        Validations.validate_region(region,default_region,EC2_RESOURCE)
        Validations.validate_db_name(RDS_RESOURCE,db_name,region)

    def validate_input_query_count(db_name, region, default_region, start_time, end_time):
        Validations.validate_region(region,default_region,EC2_RESOURCE)
        Validations.validate_db_name(RDS_RESOURCE,db_name,region)
        current_app.logger.info("Validating start-end datetime...")
        Validations.validate_datetime(start_time)
        Validations.validate_datetime(end_time)
        Validations.validate_endtime(end_time)
        Validations.validate_start_end_datetime(start_time,end_time)
        current_app.logger.info("Datetime Validation Successful "+ u'\u2705')