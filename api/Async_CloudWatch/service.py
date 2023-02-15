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

def extract_message_attributes(message):
    message_attributes = {}
    for i in message:
        message_attributes[i]={
            "StringValue":str(message[i]),
            "DataType":"String"
            }
    return message_attributes

def send_message_to_trigger_lambda(region,request_body,url):
    message_attributes = extract_message_attributes(request_body)
    client=create_client(SQS_RESOURCE, region)

    response = client.send_message(
        QueueUrl=url,
        MessageBody="Hello World",
        MessageDeduplicationId=get_random_number(),
        MessageGroupId=get_random_number(),
        MessageAttributes=message_attributes
    )
    
    return response['ResponseMetadata']['HTTPStatusCode']==HTTPStatus.OK
    
        
       
    

    
def convert_to_miliseconds(time):
    end_time = time
    datetime_format = '%Y-%m-%dT%H:%M'
    formatted_time = datetime.strptime(end_time, datetime_format)
    time_in_miliseconds = int(formatted_time.timestamp())*1000
    return time_in_miliseconds



