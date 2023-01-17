from datetime import datetime

start_time = datetime.strptime(
    '17/1/2023 11:13:08.230010', '%d/%m/%Y %H:%M:%S.%f')
end_time = datetime.strptime(
    '17/1/2023 11:13:10.230010', '%d/%m/%Y %H:%M:%S.%f')
diff = end_time-start_time
mill = diff.total_seconds() * 1000

print("Seconds: ",mill)
