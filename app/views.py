import os
import arrow
import ohapi
import requests
import urllib.parse
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import login, logout
from django.shortcuts import render, redirect, reverse

from app.decorators import member_required
from app.models import OpenHumansMember, OuraUser
from .tasks import update_oura_history
from .helpers import get_download_url

OURA_BASE_URL = 'https://api.ouraring.com/v1'


def info(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'info.html')


def about(request):
    return render(request, 'about.html')


def authorize(request):
    return redirect(ohapi.api.oauth2_auth_url(
        client_id=os.getenv('OHAPI_CLIENT_ID'),
        redirect_uri=request.build_absolute_uri(reverse('authenticate'))
    ))


def authenticate(request):
    res = ohapi.api.oauth2_token_exchange(
        client_id=os.getenv('OHAPI_CLIENT_ID'),
        client_secret=os.getenv('OHAPI_CLIENT_SECRET'),
        redirect_uri=request.build_absolute_uri(reverse('authenticate')),
        code=request.GET.get('code'),
    )

    oh_id = ohapi.api.exchange_oauth2_member(
        access_token=res['access_token']
    )['project_member_id']

    member = OpenHumansMember.objects.get_or_create(
        user=User.objects.update_or_create(username=oh_id)[0],
        oh_id=oh_id,
        defaults={
            'access_token': res['access_token'],
            'refresh_token': res['refresh_token'],
            'expiration_time': arrow.utcnow().shift(
                seconds=res['expires_in']
            ).datetime
        }
    )[0]

    login(request, member.user)
    return redirect('dashboard')


def oura_authorize(request):
    auth_endpoint = 'https://cloud.ouraring.com/oauth/authorize?'
    scopes = [
        'personal',
        'daily',
    ]
    auth_params = {
        'client_id': os.getenv('OURA_CLIENT_ID'),
        'redirect_uri': request.build_absolute_uri(
            reverse('oura_authenticate')),
        'scope': ' '.join(scopes),
        'response_type': 'code',
        'state': os.getenv('SECRET_KEY')
    }
    return redirect(auth_endpoint + urllib.parse.urlencode(auth_params))


def oura_authenticate(request):

    if request.GET.get('state') != os.getenv('SECRET_KEY') \
            or request.GET.get('error'):
        return redirect('info')

    res = requests.post('https://api.ouraring.com/oauth/token',
                        data={
                            'grant_type': 'authorization_code',
                            'code': request.GET.get('code'),
                            'redirect_uri': request.build_absolute_uri(
                                reverse('oura_authenticate')),
                            'client_id': os.getenv('OURA_CLIENT_ID'),
                            'client_secret': os.getenv('OURA_CLIENT_SECRET')
                        }).json()

    OuraUser.objects.get_or_create(
        user=request.user,
        defaults={
            'access_token': res['access_token'],
            'refresh_token': res['refresh_token'],
            'expiration_time': arrow.utcnow().shift(
                seconds=res['expires_in']
            ).datetime
        }
    )
    update_oura_history.delay(request.user.oh_member.oh_id)
    return redirect('dashboard')


@member_required
def dashboard(request):
    if hasattr(request.user, 'oura_user'):
        oura_user = request.user.oura_user
    else:
        oura_user = None
    return render(
        request,
        'dashboard.html',
        {'oura_user': oura_user,
         'archive_url': get_download_url(request.user.oh_member)})


@member_required
def oura_delink(request):
    if request.method == "POST":
        request.user.oura_user.delete()
        return redirect('dashboard')


@member_required
def delete_user(request):
    if request.method == "POST":
        request.user.delete()
        return redirect('info')


@member_required
def update_archive(request):
    if request.method == "POST":
        update_oura_history.delay(request.user.oh_member.oh_id)
        return redirect('dashboard')


def log_out(request):
    if request.method == "POST":
        logout(request)
    return redirect('info')
