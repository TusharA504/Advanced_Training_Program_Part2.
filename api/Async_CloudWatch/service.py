from datetime import datetime
import re
import boto3
from ..settings import aws_secret_access_key, aws_access_key_id,region_name
from http import HTTPStatus
from ..constant import *
from botocore.exceptions import ClientError
from flask import current_app
import random
from ..utils import create_client


def get_random_number():
    random_number = random.randint(10000, 99999)
    return str(random_number)

def send_message_to_trigger_lambda(region,message,url):
        client=create_client(SQS_RESOURCE, region)
        response = client.send_message(
            QueueUrl=url,
            MessageBody=str(message),
            MessageDeduplicationId=get_random_number(),
            MessageGroupId=get_random_number()
        )
        return response['ResponseMetadata']['HTTPStatusCode']==HTTPStatus.OK
    
        
       
    

    
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
    
    logGroups = [logGroup['logGroupName']for logGroup in response['logGroups']]
    
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
   
