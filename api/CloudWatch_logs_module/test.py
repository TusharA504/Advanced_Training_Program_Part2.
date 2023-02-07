from datetime import datetime, timedelta


tk = '2023-01-25T11:13:59.471096Z'
date, time = tk.split('T')
print(time[9:13])
normalized_date = datetime.strptime(date, '%Y-%m-%d').strftime('%d/%m/%Y')
print(normalized_date)
normalized_time = datetime.strptime(f'{normalized_date} {time[:8]}', '%d/%m/%Y %H:%M:%S') + timedelta(hours=5,minutes=30)
normalized_datetime = f"{normalized_time.strftime('%d/%m/%Y %H:%M:%S')}.{time[9:13]}"
print(normalized_datetime)