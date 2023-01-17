from datetime import datetime

def convert_to_miliseconds(endTime):
    start_time = '1/1/1970 00:00:00.0000'
    end_time = endTime
    datetime_format = '%d/%m/%Y %H:%M:%S.%f'
    
    start_time_formatted = datetime.strptime(start_time,datetime_format)
    end_time_formatted = datetime.strptime(end_time, datetime_format)

    diff = end_time_formatted - start_time_formatted
    print(diff.total_seconds())
    time_in_miliseconds = diff.total_seconds() * 1000
    return int(time_in_miliseconds)
# start_time = datetime.strptime(
#     '17/1/2023 11:13:08.230010', '%d/%m/%Y %H:%M:%S.%f')
# end_time = datetime.strptime(
#     '17/1/2023 11:13:10.230010', '%d/%m/%Y %H:%M:%S.%f')
# diff = end_time-start_time
# mill = diff.total_seconds() * 1000

# print("Seconds: ", mill)


