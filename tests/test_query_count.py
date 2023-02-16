import pytest
import requests

from datetime import datetime,timedelta

# api url
base_url = "http://127.0.0.1:5002/api/cloudwatch/log/"

# test cases for create rds instance


class TestQueryCountApi():

    route = "querycount"
    # request body

    request_obj = {
        "db_name":"database-3",
        "start_time": "14/02/2023 14:50:00.0000",
        "end_time": "14/02/2023 15:58:00.0000",
        "region":"us-east-1"
    }

    # positive test case

    def test_query_count(self):
        response = requests.post(base_url+self.route, json=self.request_obj)
        assert response.status_code == 200
        assert response.json()["TotalCount"]==5

    # negative test cases
    # db_name validation
    def test_db_name_validation(self):
        response = requests.post( base_url+self.route, json={"db_name": "database", "region": "us-east-1"})
        assert response.status_code == 400
        assert response.json()["Error"] == "Validationerror: DB name 'database' was not found. DB does not exists or exists in another region"

    # region validation
    def test_region_validation(self):
        response = requests.post(base_url+self.route, json={"db_name": "database-2", "region": "us-east"})
        assert response.status_code == 400
        assert response.json()["Error"] == "Validationerror: Invalid Region. Please enter a valid region."

    # start time validation
    def test_start_time_validation(self):
      
        response = requests.post(
            base_url+self.route, json={
                "db_name":"database-2",
                "start_time": "25-01-2023 15:45:30.0000",
                "end_time": "26/01/2023 16:57:00.0000",
                "region":"us-east-1",
            })
        assert response.status_code == 400
        assert response.json()["Error"] == "Validationerror: Invaild date time format. Please enter the datetime in this format: dd/mm/yyyy HH:MM:SS.0000"
    
    # end time validation
    def test_end_time_validation(self):
        response = requests.post(
            base_url+self.route, json={
                "db_name":"database-2",
                "start_time": "25/01/2023 15:45:30.0000",
                "end_time": "26-01-2023 16:57:00.0000",
                "region":"us-east-1",
            })
        assert response.status_code == 400
        assert response.json()[
            "Error"] == "Validationerror: Invaild date time format. Please enter the datetime in this format: dd/mm/yyyy HH:MM:SS.0000"
    
    # testing start time greater than end time
    def test_start_time_greater_than_end_time(self):
        current_time = datetime.now()
        response = requests.post(
            base_url+self.route, json={
                "db_name":"database-3",
                "start_time": "02/02/2023 15:45:30.0000",
                "end_time": "31/01/2023 16:57:00.0000",
                "region":"us-east-1"
            })
        assert response.status_code == 400
        assert response.json()[
            "Error"] == f"Validationerror: Invalid DateTime Window. Start time cannot be greater than end time."
    
    # testing end time greater than current time
    def test_end_time_greater_than_current_time(self):
        # currentTime = datetime.now()
        # endTime = str((currentTime + timedelta(hours=1)).strftime("%d/%m/%Y %H:%M:%S"))
        endTime = "25/01/2030 15:45:30.0000"
        

        response = requests.post(
            base_url+self.route, json={
                "db_name":"database-3",
                "start_time": "25/01/2023 15:45:30.0000",
                "end_time": endTime,
                "region":"us-east-1"
            })
        assert response.status_code == 400
        assert response.json()["Error"][:-7] == f"Validationerror: The entered end time is ahead of current time. Please enter end datetime before {str(datetime.now())[:-7]}."


if __name__ == "__main__":
    pytest.main()
