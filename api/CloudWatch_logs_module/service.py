from datetime import datetime, timedelta
import re
from ..settings import aws_secret_access_key, aws_access_key_id,region_name
from http import HTTPStatus
from .constant import *
from flask import current_app
from .model import *



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


def find_query_count(logGroupType,events,region):
    queries = {"TOTAL_QUERIES":0}
    for event in events:
        if logGroupType == "slowquery":
            query = (event['message'].split('\n')[-1]).split()[0]
            execution_time = event['message'].split('\n')[0].split()[-1]
            logStream_id = get_logStream_id(event['logStreamName'], region)
            insert_query_changes_to_db(logStream_id,execution_time,query,region)

            if query.upper() in queries.keys():
                queries[query.upper()] += 1
                queries['TOTAL_QUERIES'] += 1
            elif query.isalpha():
                queries[query.upper()] = 1
                queries['TOTAL_QUERIES'] += 1

        elif logGroupType == "general":
            new = event['message'].split()
            st = normalize_datetime_str(new[0])
            current_app.logger.info(st)
            query = new[3]

            if query.upper() in queries.keys():
                queries[query.upper()] += 1
                queries['TOTAL_QUERIES'] += 1
            elif query.isalpha():
                queries[query.upper()] = 1
                queries['TOTAL_QUERIES'] += 1
 
    return queries

# Changes the datetime format (yyyy-mm-ddThh:mm:ss.000000Z) => (dd/mm/yyyy HH:MM:SS.0000) 
def normalize_datetime_str(date_time):
    date, time = date_time.split('T')
    normalized_date = datetime.strptime(date, '%Y-%m-%d').strftime('%d/%m/%Y')
    normalized_time = datetime.strptime(f'{normalized_date} {time[:8]}', '%d/%m/%Y %H:%M:%S') + timedelta(hours=5,minutes=30)
    normalized_datetime = f"{normalized_time.strftime('%d/%m/%Y %H:%M:%S')}.{time[9:13]}"
    return normalized_datetime


# Checkes if the DB name in that region exists in the database. 
def DbExists(db_name,region):
    db_instance = DBInstances.query.filter_by(db_name=db_name,region=region).first()
    return db_instance is not None

# Finds the DB id by using the DB name
def get_db_id(db_name,region):
    db_instance = DBInstances.query.filter_by(db_name=db_name,region=region).first()
    db_id = db_instance.id
    return db_id

def get_logGroup_id(log_group,region):
    logGroup = LogGroups.query.filter_by(log_group=log_group,region=region).first()
    logGroup_id = logGroup.id
    return logGroup_id

def get_logStream_id(log_stream,region):
    logStream = LogStreams.query.filter_by(log_streams=log_stream,region=region).first()
    logStream_id = logStream.id
    return logStream_id

# Returns the logGroups of particular DB
def get_log_groups_of_db(db_name,region):
    db_id = get_db_id(db_name,region)
    logGroups = LogGroups.query.filter_by(db_id=db_id,region=region).all()
    logGroups_list = [log_grp.log_group for log_grp in logGroups]
    return logGroups_list

def get_logStreams_of_logGroup(log_group,region):
    logGroup_id = get_logGroup_id(log_group,region)
    log_Streams = LogStreams.query.filter_by(logGroup_id=logGroup_id,region=region).all()
    logStreams_list = [log_stream.log_streams for log_stream in log_Streams] if log_Streams else []
    return logStreams_list

# Returns new logGroups and deleted logGroups if any 
def getLogGroupsChanges(db_id,log_groups,region):
    logGroups = LogGroups.query.filter_by(db_id=db_id,region=region).all()
    logGroups_list = [log_grp.log_group for log_grp in logGroups] if logGroups else []
    new_logGroups = list(set(log_groups).difference(logGroups_list))
    deleted_logGroups = list(set(logGroups_list).difference(log_groups))
    return new_logGroups,deleted_logGroups

def getLogStreamChanges(logGroup,logStreams,region):
    logStreams_list = get_logStreams_of_logGroup(logGroup,region)
    new_logStreams = list(set(logStreams).difference(logStreams_list))
    deleted_logStreams = list(set(logStreams_list).difference(logStreams))
    return new_logStreams, deleted_logStreams



def get_queries_between(start_time,end_time,db_name,region):
    current_app.logger.info("1")
    if DbExists(db_name,region):
        current_app.logger.info("2")
        query_logs = {}
        current_app.logger.info("3")
        logGroups = get_log_groups_of_db(db_name,region)
        current_app.logger.info("4")
        for logGroup in logGroups:
            current_app.logger.info("logGrp loop start")
            logStreams = get_logStreams_of_logGroup(logGroup,region)
            current_app.logger.info("lG 1")
            queries = {"TOTAL_QUERIES":0}
            current_app.logger.info("lG 2")
            for logStream in logStreams:
                current_app.logger.info("logStr loop start")
                logStream_id = get_logStream_id(logStream,region)
                current_app.logger.info("lS 1")
                Querys = Queries.query.filter(
                    Queries.logStream_id==logStream_id, 
                    Queries.execution_time_in_ms>=start_time,
                    Queries.execution_time_in_ms<=end_time,
                    Queries.region == region
                    ).all()
                current_app.logger.info("lS 2")
                queries_list = [Query.query_statement for Query in Querys] if Querys else []
                current_app.logger.info("lS 3")
                for query in queries_list:
                    current_app.logger.info("Query loop start")
                    if query.upper() in queries.keys():
                        queries[query.upper()] += 1
                        queries['TOTAL_QUERIES'] += 1
                    elif query.isalpha():
                        queries[query.upper()] = 1
                        queries['TOTAL_QUERIES'] += 1
            query_logs[f"{logGroup.split('/')[-2]} ({logGroup.split('/')[-1]})"] = queries
        return query_logs
    raise Exception(f"DB Instance with name '{db_name}' was not found in database")


# Inserts the changes of logGroups in DataBase
def insert_logGroup_or_db_changes_to_db(db_name,log_groups,region,db_status):
    if not DbExists(db_name,region):
        current_app.logger.info(f"Adding DB Instance '{db_name}' in '{region}' region to DataBase")
        db_instance = DBInstances(db_name,region,db_status)
        db.session.add(db_instance)
        db.session.commit()
    db_id = get_db_id(db_name,region)
    new_logGroups,deleted_logGroups = getLogGroupsChanges(db_id,log_groups,region)
    if new_logGroups:
        for new_log_group in new_logGroups:
            current_app.logger.info(f"Adding LogGroup '{new_log_group}' for DB '{db_name}' of '{region}' region to DataBase")
            logGroup = LogGroups(db_id,new_log_group,region)
            db.session.add(logGroup)
            db.session.commit()
    if deleted_logGroups:
        for del_log_group in deleted_logGroups:
            current_app.logger.info(f"Deleting LogGroup '{new_log_group}' for DB '{db_name}' of '{region}' region from DataBase")
            LogGroup =LogGroups.query.filter_by(log_group=del_log_group,region=region).first()
            db.session.delete(LogGroup)
            db.session.commit()

def insert_logstream_changes_to_db(logGroup,logStream,region):
    logGroup_id = get_logGroup_id(logGroup,region)
    new_logStreams, deleted_logStreams = getLogStreamChanges(logGroup,logStream,region)
    if new_logStreams:
        for new_logStream in new_logStreams:
            current_app.logger.info(f"Adding LogStream '{new_logStream}' for '{logGroup}' Log Group of '{region}' region to DataBase")
            LogStream = LogStreams(logGroup_id,new_logStream,region)
            db.session.add(LogStream)
            db.session.commit()
    if deleted_logStreams:
        for del_log_stream in deleted_logStreams:
            current_app.logger.info(f"Deleting LogStream '{new_logStream}' for '{logGroup}' Log Group of '{region}' region from DataBase")
            logStream = LogStreams.query.filter_by(log_streams=del_log_stream,region=region).first()
            db.session.delete(logStream)
            db.session.commit()            

def insert_query_changes_to_db(logStream_id,ExecutionTime,query_statement,region):
    execution_time = normalize_datetime_str(ExecutionTime)
    execution_time_in_ms = convert_to_miliseconds(execution_time)

    Query = Queries.query.filter_by(
        execution_time_in_ms=execution_time_in_ms,
        logStream_id=logStream_id,
        query_statement=query_statement,
        region=region
    ).all()
    
    if not Query:
        query = Queries(str(execution_time_in_ms),logStream_id,query_statement,region)
        db.session.add(query)
        db.session.commit()