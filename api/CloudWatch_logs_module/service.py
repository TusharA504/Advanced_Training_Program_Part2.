from datetime import datetime
import re
from ..settings import aws_secret_access_key, aws_access_key_id,region_name
from http import HTTPStatus
from .constant import *
from botocore.exceptions import ClientError
from flask import current_app
from .rds_model import *
from ..utils import create_client


# for deleteting instance from db
def delete_database_if_not_present_at_aws(db_name,region):
    instance = Database.query.filter_by(DBName=db_name, Region=region).all()
  
    if len(instance) > 0:
        log_groups = log_groups_response(instance[0].id, region, LogGroups)
     
        for group in log_groups:
            delete_logs_groups_if_not_present_at_aws(group, region)

        db.session.query(Database).filter( Database.DBName == instance[0].DBName, Database.id == instance[0].id).delete(synchronize_session=False)
        db.session.commit()


# for deleting log_groups from db
def delete_logs_groups_if_not_present_at_aws(group,region):
    log_g = LogGroups.query.filter_by(LogGroupName=group, Region=region).all()
    log_streams = Streams.query.filter_by(LogGroupId=log_g[0].id, Region=region).all()

    for stream in log_streams:
        delete_log_streams_if_not_present_at_aws(stream)

    db.session.query(LogGroups).filter(LogGroups.LogGroupName == group).delete(synchronize_session=False)
    db.session.commit()


# for deleting log_streams from db
def delete_log_streams_if_not_present_at_aws(stream):
        db.session.query(Queries).filter( Queries.StreamId == stream[0].id).delete(synchronize_session=False)
        db.session.query(Streams).filter(Streams.id == stream[0].id).delete(synchronize_session=False)
        db.session.commit()


def convert_to_miliseconds(time):
    
    end_time = time
    datetime_format = "%Y-%m-%dT%H:%M"
   
    formatted_time = datetime.strptime(end_time, datetime_format)
    time_in_miliseconds = int(formatted_time.timestamp())*1000
    return time_in_miliseconds


def get_all_databases(region):
    client = create_client("rds", region)
    response = client.describe_db_instances()
    
    current_app.logger.info(f"Validating Response..")
    if response["ResponseMetadata"]["HTTPStatusCode"] != HTTPStatus.OK:
        raise Exception("Unexpected Error Occured")
    
    current_app.logger.info("Response Validation Successful " + u'\u2705')
    
    databases_from_aws = [instance["DBInstanceIdentifier"] for instance in response["DBInstances"]]

    databases_from_db = Database.query.filter_by(Region=region).all()

    databases_from_db = [instance.DBName for instance in databases_from_db]
    

    for instance in databases_from_db:
        if instance in databases_from_aws:
            get_instance_from_aws = client.describe_db_instances(DBInstanceIdentifier=instance)
            Database.query.filter_by(DBName = instance,Region=region).update(dict(Status=get_instance_from_aws["DBInstances"][0]["DBInstanceStatus"]))
            db.session.commit()

        else:
            delete_database_if_not_present_at_aws(instance, region)

    db_response = Database.query.filter_by(Region=region).all()
    for instance in databases_from_aws:
        if not instance in databases_from_db:
            get_instance_from_aws = client.describe_db_instances(DBInstanceIdentifier=instance)
            get_instance_from_aws=get_instance_from_aws["DBInstances"][0]
            DBInstance = Database(get_instance_from_aws["DBInstanceIdentifier"], get_instance_from_aws["DBInstanceStatus"], region)
            db.session.add(DBInstance)
            db.session.commit()
            db_response = Database.query.filter_by(Region=region).all()

    return db_response



def get_all_regions():
    current_app.logger.info(f"Creating EC2 Resource client for get all regions: {region_name}")
    ec2_client = create_client("ec2", region_name)
    response = ec2_client.describe_regions(AllRegions=True)
    return response



def describe_log_groups(client,db_name):

    response = client.describe_log_groups(
        logGroupNamePrefix=f'/aws/rds/instance/{db_name}'

    )
    
    current_app.logger.info(f"Validating Response..")
    if not response['ResponseMetadata']['HTTPStatusCode']==HTTPStatus.OK:
        raise Exception("Unexpected Error Occured")
    
    current_app.logger.info("Response Validation Successful " + u'\u2705')
    logGroups = [logGroup['logGroupName']
                 for logGroup in response['logGroups']]
    
    return logGroups


def log_groups_response(db_id,region,model):
    log_response = model.query.filter_by(DBId=db_id, Region=region).all()
    log_groups = [log_group.LogGroupName for log_group in log_response]
    return log_groups



# method to add and get log groups from db
def db_logs_response_method(db_name,region,logGroups_from_aws):
   
    # checks rds_instance exists or not in the database
    db_response = Database.query.filter_by(DBName=db_name, Region=region).all()

    # if rds_instance not exists then creating row for it
    if not len(db_response) > 0:
        get_instance_from_aws = client.describe_db_instances(DBInstanceIdentifier=db_name)
        DBInstance = Database(db_name,get_instance_from_aws["DBInstances"][0]["DBInstanceStatus"], region)
        db.session.add(DBInstance)
        db.session.commit()
        db_response = Database.query.filter_by(DBName=db_name, Region=region).all()
    
    db_id=db_response[0].id
    
    log_groups_from_database = log_groups_response(db_id, region, LogGroups)

    if len(log_groups_from_database) > 0:
        for group in log_groups_from_database:
            if not group in logGroups_from_aws:
               delete_logs_groups_if_not_present_at_aws(group,region)

    log_groups_from_database = log_groups_response(db_id, region, LogGroups)

    for group in logGroups_from_aws:
        if not group in log_groups_from_database:
            LogGroup = LogGroups(db_id, group, region)
            db.session.add(LogGroup)
            db.session.commit()
    
    
    return log_groups_response(db_id, region, LogGroups)


# method to get and add streams to database
def db_streams_response_method(client,region,logGroups_from_aws):
    log_streams_for_db = []
    for group in logGroups_from_aws:
        current_app.logger.info("Calling describe_log_streams method")
        streams_from_aws = client.describe_log_streams(logGroupName=group)
        list_streams_from_aws = [stream["logStreamName"]for stream in streams_from_aws["logStreams"]]

        log_group = LogGroups.query.filter_by(LogGroupName=group, Region=region).all()

        streams_from_db = Streams.query.filter_by(LogGroupId=log_group[0].id, Region=region).all()
        list_streams_from_db = [stream.LogStreamName for stream in streams_from_db]

        for stream in list_streams_from_db:
            if stream not in list_streams_from_aws:
                stream_r = Streams.query.filter_by(LogGroupId=log_group[0].id, LogStreamName=stream, Region=region).all()
                delete_log_streams_if_not_present_at_aws(stream_r)

        for stream in list_streams_from_aws:
            if stream not in list_streams_from_db:
                add_stream = Streams(log_group[0].id, stream, region)
                db.session.add(add_stream)
                db.session.commit()

        get_log_streams = Streams.query.filter_by(LogGroupId=log_group[0].id, Region=region).all()

        for stream in get_log_streams:
            log_streams_for_db.append( {"streamName": stream.LogStreamName, "logGroupName": log_group[0].LogGroupName})

    return log_streams_for_db



# method for add and get queries from db
def db_queries_response_method(client,logGroup_for_query_count,start_time_miliseconds,end_time_miliseconds,region):
    response=[]
    query_count = {}

    if len(logGroup_for_query_count) > 0:
        streams_from_aws = client.describe_log_streams(logGroupName=logGroup_for_query_count[0].LogGroupName)

        streams_from_aws = [stream["logStreamName"]for stream in streams_from_aws["logStreams"]]

        if len(streams_from_aws) > 0:
            # Calling filter_log_events method
            current_app.logger.info("Calling filter_log_events method")
            response = client.filter_log_events(
                logGroupName=logGroup_for_query_count[0].LogGroupName,
                logStreamNames=streams_from_aws,
                startTime=start_time_miliseconds,
                endTime=end_time_miliseconds,
               )

            # Accessing events
            response = response['events']
            
           

            for query in response:
                stream_from_db = Streams.query.filter_by( LogGroupId=logGroup_for_query_count[0].id, LogStreamName=query["logStreamName"], Region=region).all()

                query_type = query["message"].split(",")[-4].split(" ")[0].split("'")[1]

                query_from_db = Queries.query.filter_by(StreamId=stream_from_db[0].id, Message=query["message"], QueryType=query_type.upper(), QueryTime=query["timestamp"], Region=region).all()

                if len(query_from_db) == 0:
                    add_query = Queries(stream_from_db[0].id, query["message"], query_type.upper(), query["timestamp"], region)
                    db.session.add(add_query)
                    db.session.commit()
                    query_from_db = Queries.query.filter_by(StreamId=stream_from_db[0].id, Message=query["message"], QueryType=query_type.upper(), QueryTime=query["timestamp"], Region=region).all()

                if query_from_db[0].QueryType in query_count.keys():
                    query_count[query_from_db[0].QueryType] += 1

                else:
                    query_count[query_from_db[0].QueryType] = 1
        
          
            

    queries = []

    for query, count in query_count.items():
        queries.append({"query": query, "count": count})

    return {"totalQuries": len(response), "queryCount": queries}


