from datetime import datetime, timedelta
import re
from ..settings import aws_secret_access_key, aws_access_key_id,region_name
from http import HTTPStatus
from .constant import *
from flask import current_app
from .model import *
import string
from api.utils import *



def convert_to_miliseconds(time):
    end_time = time
    datetime_format = '%d/%m/%Y %H:%M:%S.%f'
    formatted_time = datetime.strptime(end_time, datetime_format)
    time_in_miliseconds = int(formatted_time.timestamp())*1000
    return time_in_miliseconds



def describe_log_groups(region,db_name):
    client = create_client(LOGS_RESOURCE,region)
    response = client.describe_log_groups(logGroupNamePrefix=f'/aws/rds/instance/{db_name}')
    if not response['ResponseMetadata']['HTTPStatusCode']==HTTPStatus.OK:
        raise Exception("Unexpected Error")

    logGroups = [logGroup['logGroupName'] for logGroup in response['logGroups']]
    
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

# ================================(Methods to check the DB changes)================================
# Finds the DB id by using the DB name
def get_db_id(db_name,region):
    db_instance = DBInstances.query.filter_by(db_name=db_name,region=region).first()
    db_id = db_instance.id
    return db_id

# Finds the DB name by using the DB id
def get_db_name(db_id):
    db_instance = DBInstances.query.filter_by(id=db_id).first()
    db_name = db_instance.db_name
    return db_name

# Adds new DBInstance to Database
def addDB(db_name,region,status,engine,is_active):
    db_instance = DBInstances(db_name,region,status,engine,is_active)
    db.session.add(db_instance)
    db.session.commit()

# Deletes DBInstance from Database
def deleteDB(db_name,region):
    db_instance = DBInstances.query.filter(DBInstances.db_name==db_name,DBInstances.region==region).first()
    db_instance.is_active = False
    db.session.commit()

# Updates the status of the existing DBInstance in database
def updateDBStatus(db_name,region,status):
    db_instance = DBInstances.query.filter(DBInstances.db_name==db_name,DBInstances.region==region).first()
    db_instance.status = status
    db.session.commit()

# Gets list of DBInstances and their info form AWS
def describe_all_awsdb_at(region):
    rds_client = create_client(RDS_RESOURCE,region)
    db_instances = rds_client.describe_db_instances()
    db_info_list = {}
    if db_instances['DBInstances']:
        for db in db_instances['DBInstances']:
            db_info = {
                'db_name':db['DBInstanceIdentifier'],
                'engine':db['Engine'],
                'status':db['DBInstanceStatus']
            }
            db_info_list[db['DBInstanceIdentifier']]=db_info
    return db_info_list

# Gets list of DBInstances and their info form Database
def describe_all_localdb_at(region):
    databases = DBInstances.query.filter(DBInstances.region==region,DBInstances.is_active==True).all()
    db_list = {}
    for database in databases:
        db_list[database.db_name] = {
            'db_name':database.db_name,
            'engine':database.engine,
            'status':database.status
        }
    return db_list

def add_live_changes_to_db(db_aws_info_list,db_local_info_list,region):
    db_aws_list = list(db_aws_info_list.keys())
    db_local_list = list(db_local_info_list.keys())
    deleted_db = list(set(db_local_list).difference(db_aws_list))
    current_app.logger.info(f"Deleted Db: {deleted_db}")
    for db in db_aws_list:
        current_app.logger.info(f"Looking for DB '{db}' in Database")
        db_instance = DBInstances.query.filter(DBInstances.region==region,DBInstances.db_name==db,DBInstances.is_active==True).all()
        current_app.logger.info(f"is db_instance? : {db_instance is True}")
        current_app.logger.info(f"db_instance is : {db_instance}")
        current_app.logger.info(f"db_instance is : {type(db_instance)}")
        if db_instance:
            current_app.logger.info(f"Found '{db}' in Database")
            awdb = describe_all_aws_loggroups_at(region,db)
            current_app.logger.info(f"AWDB was FOUND!!!!")
            for dbInstance in db_instance:
                if dbInstance.status!=db_aws_info_list[db]['status']:
                    current_app.logger.info(f"Changing status of '{db}'")
                    updateDBStatus(db,region,db_aws_info_list[db]['status'])

        elif not db_instance:
            current_app.logger.info(f"Not Found '{db}' in Database")
            current_app.logger.info(f"Adding '{db}' in Database")
            addDB(db,region,db_aws_info_list[db]['status'],db_aws_info_list[db]['engine'],True)
            aws_loggroups = describe_all_aws_loggroups_at(region,db)
            for loggroup in aws_loggroups[db]['lg_name']:
                db_id = get_db_id(db,region)
                addLG(db_id,region,loggroup)
                lg_name = loggroup.split('/')[-1]
                aws_logstreams = describe_all_aws_logstreams_at(region,lg_name,db)
                for logstream in aws_logstreams[lg_name]['ls_name']:
                    lg_id = get_logGroup_id(loggroup,region)
                    addLS(lg_id,region,logstream)

    if deleted_db:
        for del_db in deleted_db:
            deleteDB(del_db,region) 

            

# ========================================================================================================

# ================================(Methods to check the log Group changes)================================

# Adds new Log Group to Database
def addLG(db_id,region,lg_name):
    log_group = LogGroups(db_id,lg_name,region)
    db.session.add(log_group)
    db.session.commit()

# Deletes Log Group from Database
def deleteLG(db_id,region,lg_name):
    # db_id = get_db_id(db_name,region)
    log_group = LogGroups.query.filter(LogGroups.db_id==db_id,LogGroups.region==region,LogGroups.log_group==lg_name).first()
    log_group.is_active = False
    db.session.commit()

def get_logGroup_id(log_group,region):
    logGroup = LogGroups.query.filter_by(log_group=log_group,region=region).first()
    logGroup_id = logGroup.id
    return logGroup_id

def describe_all_aws_loggroups_at(region,db_name):
    rds_client = create_client(LOGS_RESOURCE,region)
    log_groups = rds_client.describe_log_groups(logGroupNamePrefix=f'/aws/rds/instance/{db_name}')
    lg_info_list = {}
    if log_groups['logGroups']:
        for log_group in log_groups['logGroups']:
            lg_url = (log_group['logGroupName']).split('/')
            if lg_url[-2] not in lg_info_list.keys():
                lg_info = {
                    'lg_name' : [log_group['logGroupName']],
                    'db_name' : lg_url[-2]
                }
                lg_info_list[lg_url[-2]]  = lg_info
            elif lg_url[-2] in lg_info_list.keys():
                (lg_info_list[lg_url[-2]]['lg_name']).append(log_group['logGroupName'])
    return lg_info_list

def describe_all_local_loggroups_at(region,db_name):
    filters = {"region":region,"is_active":True}
    if db_name:
        db_id = get_db_id(db_name,region)
        filters["db_id"] = db_id
    logGroups = LogGroups.query.filter_by(**filters).all()
    lg_info_list = {}
    if logGroups:
        for log_group in logGroups:
            db_name = get_db_name(log_group.db_id)
            if db_name not in lg_info_list.keys():
                lg_info = {
                    'lg_name' : [log_group.log_group],
                    'db_name' : db_name
                }
                lg_info_list[db_name]  = lg_info
            elif db_name in lg_info_list.keys():
                (lg_info_list[db_name]['lg_name']).append(log_group.log_group)
    return lg_info_list

# ========================================================================================================

# ================================(Methods to check the log Streams changes)================================

# Adds new Log Stream to Database
def addLS(lg_id,region,ls_name):
    log_stream = LogStreams(lg_id,ls_name,region)
    db.session.add(log_stream)
    db.session.commit()

# Deletes Log Stream from Database
def deleteLS(lg_id,region,ls_name):
    # db_id = get_db_id(db_name,region)
    log_stream = LogStreams.query.filter(LogStreams.logGroup_id==lg_id,LogStreams.region==region,LogStreams.log_streams==ls_name).first()
    log_stream.is_active = False
    db.session.commit()

def get_logStream_id(log_stream,region):
    logStream = LogStreams.query.filter_by(log_streams=log_stream,region=region).first()
    logStream_id = logStream.id
    return logStream_id

def describe_all_aws_logstreams_at(region,loggroup,db_name):
    rds_client = create_client(LOGS_RESOURCE,region)
    log_streams = rds_client.describe_log_streams(logGroupName=f"/aws/rds/instance/{db_name}/{loggroup}")
    ls_info_list = {}
    if log_streams['logStreams']:
        for log_stream in log_streams['logStreams']:
            if loggroup not in ls_info_list.keys():
                ls_info = {
                    'ls_name' : [log_stream['logStreamName']],
                    'lg_name' : loggroup
                }
                ls_info_list[loggroup]  = ls_info
            elif loggroup in ls_info_list.keys():
                (ls_info_list[loggroup]['ls_name']).append(log_stream['logStreamName'])
    return ls_info_list

def describe_all_local_logstreams_at(region,loggroup,db_name):
    db_id = get_db_id(db_name,region)
    filters = {"region":region,"is_active":True,"db_id":db_id}
    if loggroup:
        # lg_id = get_logGroup_id(loggroup,region)
        filters["log_group"] = f"/aws/rds/instance/{db_name}/{loggroup}"
    logGroups = LogGroups.query.filter_by(**filters).all()
    ls_info_list = {}
    if logGroups:
        for log_group in logGroups:
            lg_id = get_logGroup_id(log_group.log_group,region)
            logGroup = (log_group.log_group).split('/')[-1]
            logStreams = LogStreams.query.filter(LogStreams.logGroup_id==lg_id).first() 
            if logGroup not in ls_info_list.keys():
                ls_info = {
                    'ls_name' : [logStreams.log_streams],
                    'lg_name' : logGroup
                }
                ls_info_list[logGroup]  = ls_info
            elif logGroup in ls_info_list.keys():
                (ls_info_list[logGroup]['ls_name']).append(logStreams.log_streams)
    return ls_info_list

# ========================================================================================================

# ================================(Methods to check the Query changes)================================

# Adds new Query log to Database
def addQuery(execution_time,db_id,query_word,region):
    query = Queries(execution_time,db_id,query_word,region)
    db.session.add(query)
    db.session.commit()

def queryExists(execution_time,db_id,query_word,region):
    current_app.logger.info("Is this problem")
    query = Queries.query.filter(
        Queries.execution_time_in_ms==execution_time,
        Queries.db_id == db_id,
        Queries.query_statement == query_word,
        Queries.region == region
    ).all()
    current_app.logger.info("Is this problem")
    return True if query else False

def describe_all_aws_querylogs_between(start_time,end_time,db_name,region):
    # Converting Start-End time to miliseconds
    start_time_miliseconds = convert_to_miliseconds(start_time)
    end_time_miliseconds = convert_to_miliseconds(end_time)
    logs_client = create_client(LOGS_RESOURCE,region)
    query_events = logs_client.filter_log_events(
        logGroupName=f"/aws/rds/instance/{db_name}/audit",
        logStreamNames=[db_name],
        startTime=start_time_miliseconds,
        endTime=end_time_miliseconds,
        filterPattern='shreeraj'
    )
    return query_events

def describe_all_local_querylogs_between(start_time,end_time,db_name,region):
    # Converting Start-End time to miliseconds
    start_time_miliseconds = convert_to_miliseconds(start_time)
    end_time_miliseconds = convert_to_miliseconds(end_time)

    db_id = get_db_id(db_name,region)
    queries_info = Queries.query.filter(
        Queries.db_id == db_id,
        Queries.execution_time_in_ms >= start_time_miliseconds,
        Queries.execution_time_in_ms <= end_time_miliseconds,
    ).all()

    queries = [query.query_statement for query in queries_info]
    return queries


def extract_query_word(message):
    split_msg = message.split(',')
    query_word = ''
    if split_msg[2]=='shreeraj' and split_msg[6]=="QUERY":
        query = split_msg[8].strip("'")
        query_word = query.split()[0]
    return query_word
