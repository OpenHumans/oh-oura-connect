from ohapi import api


def get_download_url(oh_member):
    files = api.exchange_oauth2_member(
        access_token=oh_member.get_access_token())['data']
    for f in files:
        if f['basename'] == 'oura-data.json':
            return {'url': f['download_url'], 'created': f['created']}
    return None
