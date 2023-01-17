from datetime import datetime,timezone

def convert_to_miliseconds(Time):
    end_time = Time
    datetime_format = '%d/%m/%Y %H:%M:%S.%f'
    formatted_time = datetime.strptime(end_time, datetime_format)
    time_in_miliseconds = int(formatted_time.timestamp())*1000
    return time_in_miliseconds
    

# start_time = datetime.strptime(
#     '17/1/2023 11:13:08.230010', '%d/%m/%Y %H:%M:%S.%f')
# end_time = datetime.strptime(
#     '17/1/2023 11:13:10.230010', '%d/%m/%Y %H:%M:%S.%f')
# diff = end_time-start_time
# mill = diff.total_seconds() * 1000

# print("Seconds: ", mill)


