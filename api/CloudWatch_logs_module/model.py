from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class DBInstances(db.Model):
    __tablename__ = 'db_instances'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    db_name = db.Column(db.String(63))
    region = db.Column(db.String(20))
    status = db.Column(db.String(20))
    engine = db.Column(db.String(50))


    def __init__(self, db_name, region, status,engine):
        self.db_name = db_name
        self.region = region
        self.status = status
        


class LogGroups(db.Model):
    __tablename__ = 'log_groups'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    db_id = db.Column(db.Integer, db.ForeignKey('db_instances.id'))
    log_group = db.Column(db.String(100))
    region = db.Column(db.String(20))

    def __init__(self,db_id,log_group, region):
        self.db_id = db_id
        self.log_group = log_group
        self.region = region

class LogStreams(db.Model):
    __tablename__ = 'log_streams'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    logGroup_id = db.Column(db.Integer, db.ForeignKey('log_groups.id'))
    log_streams = db.Column(db.String(100))
    region = db.Column(db.String(20))

    def __init__(self,logGroup_id,log_streams, region):
        self.logGroup_id = logGroup_id
        self.log_streams = log_streams
        self.region = region
    
class Queries(db.Model):
    __tablename__ = 'queries'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    execution_time_in_ms = db.Column(db.String(50))
    logStream_id = db.Column(db.Integer, db.ForeignKey('log_groups.id'))
    query_statement = db.Column(db.String(100))
    region = db.Column(db.String(20))

    def __init__(self,execution_time_in_ms,logStream_id,query_statement, region):
        self.execution_time_in_ms = execution_time_in_ms
        self.logStream_id = logStream_id
        self.query_statement = query_statement
        self.region = region