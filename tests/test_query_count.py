import pytest
import requests

from datetime import datetime,timedelta

# api url
base_url = "http://127.0.0.1:5001/api/cloudwatch/log/"

# test cases for create rds instance


class TestQueryCountApi():

    route = "queries"
    # request body

    request_obj = {
        "db_name": "database-1",
        "start_time": "2023-02-10T10:00",
        "end_time": "2023-02-10T20:41",
        "region": "us-east-1"
    }

    # positive test case

    def test_query_count(self):
        response = requests.post(base_url+self.route, json=self.request_obj)
        assert response.status_code == 200
        assert response.json()["totalQuries"]==6

    # negative test cases
    # db_name validation
    def test_db_name_validation(self):
        response = requests.post( base_url+self.route, json={"db_name": "database", "region": "us-east-1"})
        assert response.status_code == 400
        assert response.json()[
            "Error"] == "DB name 'database' was not found. DB does not exists or exists in another region"

    # region validation
    def test_region_validation(self):
        response = requests.post(base_url+self.route, json={"db_name": "database-1", "region": "us-east"})
        assert response.status_code == 400
        assert response.json()["Error"] == "Invalid Region. Please enter a valid region."

    # start time validation
    def test_start_time_validation(self):
      
        response = requests.post(
            base_url+self.route, json={"db_name": "database-1",
                                       "start_time": "2023-02-10T10:",
                                       "end_time": "2023-02-10T20:41",
                                       "region": "us-east-1"})
        assert response.status_code == 400
        assert response.json()["Error"] == "time data '2023-02-10T10:' does not match format '%Y-%m-%dT%H:%M'"
    
    # end time validation
    def test_end_time_validation(self):
        response = requests.post(
            base_url+self.route, json={"db_name": "database-1",
                                       "start_time": "2023-02-10T10:20",
                                       "end_time": "2023-02-1020:41",
                                       "region": "us-east-1"})
        assert response.status_code == 400
        assert response.json()[
            "Error"] == "time data '2023-02-1020:41' does not match format '%Y-%m-%dT%H:%M'"
    
    # testing start time greater than end time
    def test_start_time_greater_than_end_time(self):
        response = requests.post(
            base_url+self.route, json={"db_name": "database-1",
                                       "start_time": "2023-02-10T10:20",
                                       "end_time": "2023-02-10T09:41",
                                       "region": "us-east-1"})
        assert response.status_code == 400
        assert response.json()[
            "Error"] == "Invalid DateTime Window. Start time cannot be greater than end time."
    
    # testing end time greater than current time
    def test_end_time_greater_than_current_time(self):
        now = datetime.now() + timedelta(hours=6)
        now=now.strftime("%Y-%m-%dT%H:%M")
        response = requests.post(
            base_url+self.route, json={"db_name": "database-1",
                                       "start_time": "2023-02-10T10:20",
                                       "end_time": now,
                                       "region": "us-east-1"})
        assert response.status_code == 400
        assert response.json()[
            "Error"] == f"The entered end time is ahead of current time. Please enter end datetime before {now}."

    def test_start_time_greater_than_current_time(self):
        now = datetime.now() + timedelta(hours=6)
        now=now.strftime("%Y-%m-%dT%H:%M")
        response = requests.post(
            base_url+self.route, json={"db_name": "database-1",
                                       "start_time": now,
                                       "end_time": now,
                                       "region": "us-east-1"})
        assert response.status_code == 400
        assert response.json()[
            "Error"] == f"The entered end time is ahead of current time. Please enter end datetime before {now}."


if __name__ == "__main__":
    pytest.main()
