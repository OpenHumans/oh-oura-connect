from django.core.management.base import BaseCommand
from app.models import SpotifyUser
from app.tasks import update_play_history
import time
import requests


class Command(BaseCommand):
    help = 'Updates data for all members'

    def handle(self, *args, **options):
        # cheat to wake up sleeping worker
        requests.get('https://oh-spotify-integration.herokuapp.com/')

        spotify_users = SpotifyUser.objects.all()
        for sp in spotify_users:
            update_play_history.delay(sp.user.oh_member.oh_id)
            print('submitted update for {}'.format(sp.id))
            time.sleep(2)
