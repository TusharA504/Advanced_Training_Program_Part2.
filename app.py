from flask import Flask
import logging
from api.CloudWatch_logs_module import cloudwatch_log_bp
from api.Async_CloudWatch import async_cloudwatch_bp

app = Flask(__name__)
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
