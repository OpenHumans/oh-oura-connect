import ohapi
import json
import tempfile
import requests
from app.models import OpenHumansMember
from celery import shared_task
import datetime

OURA_BASE_URL = 'https://api.ouraring.com/v1'

OURA_V2_BASE_URL = "https://api.ouraring.com/v2/usercollection"

def simple_oura_import(oura_user):
    oura_data = {}
    access_token = oura_user.get_access_token()
    profile = requests.get(
        OURA_BASE_URL + '/userinfo?access_token={}'.format(access_token))
    if profile.status_code == 200:
        oura_data['profile'] = profile.json()
    start_date = '2015-01-01'
    end_date = str(datetime.date.today())
    sleep = requests.get(
      OURA_BASE_URL + '/sleep?start={}&end={}&access_token={}'.format(
        start_date, end_date, access_token))
    if sleep.status_code == 200:
        oura_data['sleep'] = sleep.json()['sleep']
    activity = requests.get(
      OURA_BASE_URL + '/activity?start={}&end={}&access_token={}'.format(
        start_date, end_date, access_token))
    if activity.status_code == 200:
        oura_data['activity'] = activity.json()['activity']
    readiness = requests.get(
      OURA_BASE_URL + '/readiness?start={}&end={}&access_token={}'.format(
        start_date, end_date, access_token))
    if readiness.status_code == 200:
        oura_data['readiness'] = readiness.json()['readiness']
    return oura_data

def update_v2_data(oh_member, oura_user):
    endpoints = [
        "daily_activity",
        "daily_readiness",
        "daily_sleep",
        "heartrate",
        "sessions",
        "sleep",
        "tag",
        "workout"
        ]
    for endpoint in endpoints:
        # get data
        data = get_endpoint_data(endpoint, oura_user)
        # # TODO:
        # - delete all data
        if data:
            oh_access_token = oh_member.get_access_token()
            ohapi.api.delete_file(
                file_basename='oura-v2-{}.json'.format(endpoint),
                access_token=oh_access_token)
            # - write data to OH
            with tempfile.TemporaryFile() as f:
                js = json.dumps(data)
                js = str.encode(js)
                f.write(js)
                f.flush()
                f.seek(0)
                ohapi.api.upload_stream(
                    f, "oura-v2-{}.json".format(endpoint), metadata={
                        "description": "Oura API V2 records",
                        "tags": ["oura", endpoint]
                        }, access_token=oh_access_token)
                print('updated v2 data for {}'.format(endpoint))

def get_endpoint_data(endpoint, oura_user):
    endpoint_url = OURA_V2_BASE_URL + "/" + endpoint # base endpoint
    oura_token = oura_user.get_access_token()
    headers = {"Authorization": "Bearer {}".format(oura_token)}
    data = []
    for i in range(2015, datetime.datetime.today().year+1): # iterate over all years
        r_url = endpoint_url + "?start_date={}-01-01&end_date={}-01-01".format(
            i, i+1
        )
        response = requests.get(r_url, headers=headers)
        if response.status_code == 200:
            data = data + response.json()['data']
    return data


@shared_task
def update_oura_history(oh_member_id):
    oh_member = OpenHumansMember.objects.get(oh_id=oh_member_id)
    oura_user = oh_member.user.oura_user
    print('trying to update {}/{}'.format(oura_user.id, oh_member_id))
    oura_archive = simple_oura_import(oura_user)
    with tempfile.TemporaryFile() as f:
        js = json.dumps(oura_archive)
        js = str.encode(js)
        f.write(js)
        f.flush()
        f.seek(0)
        oh_access_token = oh_member.get_access_token()
        ohapi.api.delete_file(
            file_basename='oura-data.json',
            access_token=oh_access_token)
        ohapi.api.upload_stream(
            f, "oura-data.json", metadata={
                "description": "Oura records",
                "tags": ["oura", 'activity', 'temperature', 'sleep']
                }, access_token=oh_access_token)
        print('updated v1 data for {}/{}'.format(oura_user.id, oh_member_id))
    update_v2_data(oh_member, oura_user)
    print('updated v2 data for {}/{}'.format(oura_user.id, oh_member_id))
