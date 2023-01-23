from datetime import datetime


def convert_to_miliseconds(time):
    end_time = time
    datetime_format = '%d/%m/%Y %H:%M:%S.%f'
    formatted_time = datetime.strptime(end_time, datetime_format)
    time_in_miliseconds = int(formatted_time.timestamp())*1000
    return time_in_miliseconds


def find_query_count(log_group_type, events):
    queries = {"TOTAL_QUERIES": 0}
    for event in events:
        if log_group_type == "slowquery":
            new = event['message'].split('\n')[-1]
            query = new.split()[0]
            if query.upper() in queries.keys():
                queries[query.upper()] += 1
                queries['TOTAL_QUERIES'] += 1
            elif query.isalpha():
                queries[query.upper()] = 1
                queries['TOTAL_QUERIES'] += 1
            # return event['message']
        elif log_group_type == "general":
            new = event['message'].split()
           
            # query_index = new.index("Query") if "Query" in new else None
            query = new[3]
            # new[query_index+1] 
            # if query_index else ""
            if query.upper() in queries.keys():
                queries[query.upper()] += 1
                queries['TOTAL_QUERIES'] += 1
            elif query.isalpha():
                queries[query.upper()] = 1
                queries['TOTAL_QUERIES'] += 1
            # return events 
 
    return queries
    




