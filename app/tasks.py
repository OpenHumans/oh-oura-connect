import ohapi
import json
import tempfile
import requests
from app.models import OpenHumansMember
from celery import shared_task
import os
import datetime

SPOTIFY_BASE_URL = 'https://api.spotify.com/v1'


@shared_task
def update_play_history(oh_member_id):
    oh_member = OpenHumansMember.objects.get(oh_id=oh_member_id)
    spotify_user = oh_member.user.spotify_user

    spotify_archive = get_spotify_archive(oh_member)
    spotify_archive = extend_archive(spotify_archive, spotify_user)
    if spotify_archive:
        with tempfile.TemporaryFile() as f:
            js = json.dumps(spotify_archive)
            js = str.encode(js)
            f.write(js)
            f.flush()
            f.seek(0)
            ohapi.api.delete_file(
                file_basename='spotify-listening-archive.json',
                access_token=oh_member.get_access_token())
            ohapi.api.upload_stream(
                f, "spotify-listening-archive.json", metadata={
                "description": "Spotify Play History",
                "tags": ["spotify"]
            }, access_token=oh_member.get_access_token())
        print('updated data for {}'.format(oh_member_id))


def get_spotify_archive(oh_member):
    files = ohapi.api.exchange_oauth2_member(
        access_token=oh_member.get_access_token()
    )['data']
    for f in files:
        if f['basename'] == 'spotify-listening-archive.json':
            return requests.get(f['download_url']).json()
    return []


def extend_archive(spotify_archive, spotify_user):
    response = requests.get(
        SPOTIFY_BASE_URL + '/me/player/recently-played?limit=50', headers={
        'Authorization': 'Bearer {}'.format(spotify_user.get_access_token())
    })
    if response.status_code == 429:
        update_play_history.apply_async(
                    args=[spotify_user.user.oh_member.oh_id],
                    countdown=int(response.headers['Retry-After'])+1)
        return None
    recently_played = response.json()
    if 'items' in recently_played.keys():
        recent_items = [i for i in reversed(recently_played['items'])]
        if spotify_archive:
            last_timestamp = datetime.datetime.strptime(
                                spotify_archive[-1]['played_at'],
                                '%Y-%m-%dT%H:%M:%S.%fZ')
            for entry in recent_items:
                played_at = datetime.datetime.strptime(
                            entry['played_at'], '%Y-%m-%dT%H:%M:%S.%fZ')
                if played_at > last_timestamp:
                    spotify_archive.append(entry)
            return spotify_archive
        else:
            return recent_items
    return None
