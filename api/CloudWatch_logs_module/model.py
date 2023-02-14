from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class DBInstances(db.Model):
    __tablename__ = 'db_instances'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    db_name = db.Column(db.String(63))
    region = db.Column(db.String(20))
    status = db.Column(db.String(20))
    engine = db.Column(db.String(50))
    is_active = db.Column(db.Boolean,default=True)


    def __init__(self, db_name, region, status,engine,is_active=True):
        self.db_name = db_name
        self.region = region
        self.status = status
        self.engine = engine
        self.is_active = is_active


class LogGroups(db.Model):
    __tablename__ = 'log_groups'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    db_id = db.Column(db.Integer)
    log_group = db.Column(db.String(100))
    region = db.Column(db.String(20))
    is_active = db.Column(db.Boolean,default=True)


    def __init__(self,db_id,log_group, region,is_active=True):
        self.db_id = db_id
        self.log_group = log_group
        self.region = region
        self.is_active = is_active


class LogStreams(db.Model):
    __tablename__ = 'log_streams'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    logGroup_id = db.Column(db.Integer)
    log_streams = db.Column(db.String(100))
    region = db.Column(db.String(20))
    is_active = db.Column(db.Boolean,default=True)

    def __init__(self,logGroup_id,log_streams, region,is_active=True):
        self.logGroup_id = logGroup_id
        self.log_streams = log_streams
        self.region = region
        self.is_active = is_active
    
class Queries(db.Model):
    __tablename__ = 'queries'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    execution_time_in_ms = db.Column(db.String(50))
    db_id = db.Column(db.Integer)
    query_statement = db.Column(db.String(100))
    region = db.Column(db.String(20))

    def __init__(self,execution_time_in_ms,db_id,query_statement, region):
        self.execution_time_in_ms = execution_time_in_ms
        self.db_id = db_id
        self.query_statement = query_statement
        self.region = region