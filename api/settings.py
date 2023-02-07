import os
from dotenv import load_dotenv

dotenv_path = '.env'
load_dotenv(dotenv_path)


aws_access_key_id = os.environ.get("AWS_ACCESS_KEY_ID")
aws_secret_access_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
region_name = os.environ.get("AWS_REGION")

db_username = os.environ.get("DB_USERNAME")
db_password = os.environ.get("DB_PASSWORD")
db_host = os.environ.get("DB_HOST")
db_name = os.environ.get("DB_NAME")

# aws_access_key_id = "AKIAULWWQD62DD4POH56"
# aws_secret_access_key = "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"
