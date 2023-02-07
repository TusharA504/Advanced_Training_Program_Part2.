from flask import Flask
from flask_cors import CORS
import logging
from api.CloudWatch_logs_module import cloudwatch_log_bp
from api.Async_CloudWatch import async_cloudwatch_bp
from api.extras import extras_bp
from api.CloudWatch_logs_module.model import db
from api.settings import db_username,db_name,db_password,db_host

app = Flask(__name__)
CORS(app)
app.register_blueprint(cloudwatch_log_bp)
app.register_blueprint(async_cloudwatch_bp)
app.register_blueprint(extras_bp)

# logging configuration
logging.basicConfig(filename="api.log",
                    format='%(asctime)s %(levelname)s %(message)s',
                    filemode='a', level=logging.INFO)


@app.route("/")
def hello_world():
    return "Hello, world!"

# -----(DataBase Configuration)-----
# configure the SQLite database, relative to the app instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = f"mysql+pymysql://{db_username}:{db_password}@{db_host}/{db_name}"
# initialize the app with the extension
db.init_app(app)
# Create table
with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run()