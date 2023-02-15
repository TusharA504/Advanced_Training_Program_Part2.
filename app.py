from flask import Flask
import logging
from flask_sqlalchemy import SQLAlchemy
from api.CloudWatch_logs_module import cloudwatch_log_bp
from api.Async_CloudWatch import async_cloudwatch_bp
from api.extensions import db
from flask_cors import CORS, cross_origin

app = Flask(__name__)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://admin:Password$123@localhost/boto_3_assignment_advance_part'

with app.app_context():
    db.init_app(app)
    from api.CloudWatch_logs_module.rds_model import Database
    from api.CloudWatch_logs_module.rds_model import LogGroups
    from api.CloudWatch_logs_module.rds_model import Queries
    from api.CloudWatch_logs_module.rds_model import Streams
    db.create_all()


app.register_blueprint(cloudwatch_log_bp)
app.register_blueprint(async_cloudwatch_bp)

# logging configuration
logging.basicConfig(filename="api.log",
                    format='%(asctime)s %(levelname)s %(message)s',
                    filemode='a', level=logging.INFO)


@app.route("/")
def hello_world():
    return "Hello, world!"


if __name__ == "__main__":
    app.run()
