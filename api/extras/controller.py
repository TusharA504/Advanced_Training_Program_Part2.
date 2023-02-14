from api.utils import get_regions_list,create_client
from flask import jsonify,request,current_app
from api.CloudWatch_logs_module.model import *
from api.extras.services import *

def get_region_list():
    regions = get_regions_list()
    available_regions=[]
    unavailable_regions=[]
    current_app.logger.info(f"Sorting available & unavailable regions")
    for region in regions['Regions']:
        if region['OptInStatus']=='not-opted-in':
            unavailable_regions.append(region['RegionName'])
        else:
            available_regions.append(region['RegionName'])
    current_app.logger.info(f"Removing us-east-1")
    available_regions.remove('us-east-1') if 'us-east-1' in available_regions else available_regions
    unavailable_regions.remove('us-east-1') if 'us-east-1' in unavailable_regions else unavailable_regions
    current_app.logger.info(f"Sorting lists")
    available_regions.sort()
    unavailable_regions.sort()

    # available_regions = [region['RegionName'] for region in regions['Regions'] if region[]]
    # sorted = regions_list.sort()
    current_app.logger.info(f"Returing op")

    return jsonify({'available_regions':available_regions,'unavailable_regions':unavailable_regions})

def get_db_list():
    region = request.json.get('region')
    db_instance = DBInstances.query.filter_by(region=region).all() if region else DBInstances.query.all()
    db_list = [{'name':dbs.db_name,'status':dbs.status} for dbs in db_instance]
    return jsonify(db_list)

def getter():
    rds_client = create_client(RDS_RESOURCE,)