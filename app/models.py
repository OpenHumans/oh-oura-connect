import os
import ohapi
import arrow
import requests
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings


class OpenHumansMember(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE,
                                related_name='oh_member')
    oh_id = models.CharField(max_length=16, primary_key=True)
    access_token = models.CharField(max_length=256)
    refresh_token = models.CharField(max_length=256)
    expiration_time = models.DateTimeField()

    def get_access_token(self):
        if arrow.utcnow() >= self.expiration_time:
            self.refresh_tokens()
        return self.access_token

    def refresh_tokens(self):
        res = ohapi.api.oauth2_token_exchange(
            client_id=os.getenv('OHAPI_CLIENT_ID'),
            client_secret=os.getenv('OHAPI_CLIENT_SECRET'),
            refresh_token=self.refresh_token,
            redirect_uri=settings.OH_REDIRECT_URL
        )
        self.access_token = res['access_token']
        self.refresh_token = res['refresh_token']
        self.expiration_time = arrow.utcnow().shift(
            seconds=res['expires_in']
        ).datetime
        self.save()


class OuraUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE,
                                related_name='oura_user')
    access_token = models.TextField()
    refresh_token = models.TextField()
    expiration_time = models.DateTimeField()

    def get_access_token(self):
        if arrow.utcnow() >= self.expiration_time:
            self.refresh_tokens()
        return self.access_token

    def refresh_tokens(self):
        res = requests.post('https://api.ouraring.com/oauth/token',
                            data={
                                'grant_type': 'refresh_token',
                                'client_id': os.getenv('OURA_CLIENT_ID'),
                                'client_secret': os.getenv('OURA_CLIENT_SECRET'),
                                'refresh_token': self.refresh_token
                            }).json()
        self.access_token = res['access_token']
        self.refresh_token = res['refresh_token']
        self.expiration_time: arrow.utcnow().shift(
            seconds=res['expires_in']
        ).datetime
        self.save()
