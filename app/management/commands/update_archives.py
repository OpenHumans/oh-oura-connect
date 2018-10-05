from django.core.management.base import BaseCommand
from app.models import OuraUser
from app.tasks import update_oura_history
import time
import requests


class Command(BaseCommand):
    help = 'Updates data for all members'

    def handle(self, *args, **options):
        # cheat to wake up sleeping worker
        requests.get('https://oh-oura-connect.herokuapp.com/')

        oura_users = OuraUser.objects.all()
        for sp in oura_users:
            update_oura_history.delay(sp.user.oh_member.oh_id)
            print('submitted update for {}'.format(sp.id))
            time.sleep(2)
