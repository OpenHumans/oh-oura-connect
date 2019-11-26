import ohapi
import json
import tempfile
import requests
from app.models import OpenHumansMember
from celery import shared_task
import datetime

OURA_BASE_URL = 'https://api.ouraring.com/v1'


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


@shared_task
def update_oura_history(oh_member_id):
    oh_member = OpenHumansMember.objects.get(oh_id=oh_member_id)
    oura_user = oh_member.user.oura_user
    print('trying to update {}'.format(oura_user.id))
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
        print('updated data for {}'.format(oh_member_id))
