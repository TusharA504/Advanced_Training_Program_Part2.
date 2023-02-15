from ..extensions import db


class Database(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    DBName = db.Column(db.String(50), nullable=False)
    Region = db.Column(db.String(50), nullable=False)
    Status=db.Column(db.String(50),nullable=False)

    def __init__(self,DBName,Status ,Region):
      self.DBName = DBName
      self.Region = Region
      self.Status=Status


class LogGroups(db.Model):
    id =  db.Column(db.Integer, primary_key=True)
    DBId = db.Column(db.Integer, db.ForeignKey('database.id'),nullable=False)
    LogGroupName=db.Column(db.String(50), nullable=False)
    Region = db.Column(db.String(50), nullable=False)

    def __init__(self, DBId,LogGroupName,Region):
      self.DBId= DBId
      self.LogGroupName = LogGroupName
      self.Region= Region

class Streams(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    LogGroupId=db.Column(db.Integer,db.ForeignKey('log_groups.id'),nullable=False)
    LogStreamName=db.Column(db.String(500),nullable=False)
    Region=db.Column(db.String(200),nullable=False)

    def __init__(self,LogGroupId,logStreamName,Region):
      self.LogGroupId=LogGroupId
      self.LogStreamName=logStreamName
      self.Region=Region


class Queries(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    StreamId=db.Column(db.Integer, db.ForeignKey('streams.id'),nullable=False)
    Message=db.Column(db.String(500), nullable=False)
    QueryType=db.Column(db.String(150),nullable=False)
    QueryTime=db.Column(db.BigInteger,nullable=False)
    Region = db.Column(db.String(200), nullable=False)
    

    def __init__(self, StreamId,Message,QuiryType,QueryTime,Region):
      self.StreamId= StreamId
      self.Message = Message
      self.QueryType=QuiryType
      self.QueryTime= QueryTime
      self.Region=Region
     
  