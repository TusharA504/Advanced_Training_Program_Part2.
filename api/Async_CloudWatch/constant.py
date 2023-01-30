# resources
LOGS_RESOURCE='logs'
RDS_RESOURCE='rds'
EC2_RESOURCE='ec2'
SQS_RESOURCE='sqs'

# optinstatus message

OPT_IN_NOT_REQUIRED = 'opt-in-not-required'
OPTED_IN = 'opted-in'

# que_url

QUEUE_URL= "https://queue.amazonaws.com/962020710349/Lambda_trigger.fifo"

# messages

LOG_GROUP_NOT_FOUND = "Unable to find log groups."
QUERIES_NOT_FOUND = "An error occuring while searching for queries"
INVALID_REGION = 'Invalid Region. Please enter a valid region.'
INVALID_DBNAME = "DB name '{db_name}' was not found. DB does not exists or exists in another region"
INVALID_DATETIME_FORMAT = "Invaild date time format. Please enter the datetime in this format: dd/mm/yyyy HH:MM:SS.0000"
INVALID_ENDTIME = "The entered end time is ahead of current time. Please enter end datetime before {current_time}."
INVALID_DATE_TIME_WINDOW = "Invalid DateTime Window. Start time cannot be greater than end time."
MESSAGE_SENT="Message was sent successfully. Look for the output in CloudWatch Logs"
MESSAGE_NOT_SENT = "An error occured while sending the message"


DATE_TIME_FORMAT = r"[0-3]?[0-9]/[0-1]?[0-9]/((19([7-9]?[0-9]))|20([0-9]?[0-9])) ([0-2]?[0-9]):([0-6]?[0-9]):([0-6]?[0-9]).([0-9][0-9][0-9][0-9])"
