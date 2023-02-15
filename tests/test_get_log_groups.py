import pytest
import requests

# api url
base_url = "http://127.0.0.1:5001/api/cloudwatch/log/"

# test cases for create rds instance


class TestLogGroupApi():

    route="groups"   
    # request body
    
    request_obj = {
        "db_name": "database-1",
        "region": "us-east-1"
    }
    

    # positive test case

    def test_get_log_groups(self):
        response = requests.post(base_url+self.route, json=self.request_obj)
        assert response.status_code==200
    
    # negative test cases
    # db_name validation
    def test_db_name_validation(self):
        response = requests.post(base_url+self.route, json={"db_name":"database","region":"us-east-1"})
        assert response.status_code==400
        assert response.json()["Error"]== "DB name 'database' was not found. DB does not exists or exists in another region"
    
    # region validation
    def test_region_validation(self):
        response = requests.post(base_url+self.route, json={"db_name": "database-1", "region": "us-east"})
      
        assert response.status_code == 400
        assert response.json()["Error"] == "Invalid Region. Please enter a valid region."

    


if __name__ == "__main__":
        pytest.main()    
