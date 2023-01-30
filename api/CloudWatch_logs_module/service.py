from datetime import datetime
import re
from ..settings import aws_secret_access_key, aws_access_key_id,region_name
from http import HTTPStatus
from .constant import *
from botocore.exceptions import ClientError
from flask import current_app



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
   
