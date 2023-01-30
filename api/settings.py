import os
from dotenv import load_dotenv

dotenv_path = '.env'
load_dotenv(dotenv_path)


aws_access_key_id = os.environ.get("AWS_ACCESS_KEY_ID")
aws_secret_access_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
region_name = os.environ.get("AWS_REGION")