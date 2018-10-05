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
from app.models import OpenHumansMember, SpotifyUser
from .tasks import update_play_history
from .helpers import get_download_url

SPOTIFY_BASE_URL = 'https://api.spotify.com/v1'


def info(request):
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
        user=User.objects.get_or_create(username=oh_id)[0],
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


def spotify_authorize(request):
    auth_endpoint = 'https://accounts.spotify.com/authorize?'
    scopes = [
        'streaming',
        'user-read-recently-played',
    ]
    auth_params = {
        'client_id': os.getenv('SPOTIFY_CLIENT_ID'),
        'redirect_uri': request.build_absolute_uri(
            reverse('spotify_authenticate')),
        'scope': ' '.join(scopes),
        'response_type': 'code',
        'state': os.getenv('SECRET_KEY')
    }
    return redirect(auth_endpoint + urllib.parse.urlencode(auth_params))


def spotify_authenticate(request):

    if request.GET.get('state') != os.getenv('SECRET_KEY') \
            or request.GET.get('error'):
        return redirect('info')

    res = requests.post('https://accounts.spotify.com/api/token',
                        data={
                            'grant_type': 'authorization_code',
                            'code': request.GET.get('code'),
                            'redirect_uri': request.build_absolute_uri(
                                reverse('spotify_authenticate')),
                            'client_id': os.getenv('SPOTIFY_CLIENT_ID'),
                            'client_secret': os.getenv('SPOTIFY_CLIENT_SECRET')
                        }).json()

    SpotifyUser.objects.get_or_create(
        user=request.user,
        defaults={
            'access_token': res['access_token'],
            'refresh_token': res['refresh_token'],
            'expiration_time': arrow.utcnow().shift(
                seconds=res['expires_in']
            ).datetime
        }
    )
    update_play_history.delay(request.user.oh_member.oh_id)
    return redirect('dashboard')


@member_required
def dashboard(request):
    if hasattr(request.user, 'spotify_user'):
        spotify_user = request.user.spotify_user
    else:
        spotify_user = None
    return render(
        request,
        'dashboard.html',
        {'spotify_user': spotify_user,
         'archive_url': get_download_url(request.user.oh_member)})


@member_required
def spotify_delink(request):
    if request.method == "POST":
        request.user.spotify_user.delete()
        return redirect('dashboard')


@member_required
def delete_user(request):
    if request.method == "POST":
        request.user.delete()
        return redirect('info')


@member_required
def update_archive(request):
    if request.method == "POST":
        update_play_history.delay(request.user.oh_member.oh_id)
        return redirect('dashboard')


@member_required
def recommendations(request):
    if not hasattr(request.user, 'spotify_user'):
        return redirect('spotify_authorize')
    if request.method == 'POST':
        payload = {
            'seed_genres': ','.join(request.POST.getlist('genres'))
        }

        for key, value in request.POST.items():
            value = value.split(',')
            if key.startswith('a_'):
                payload['min_{}'.format(key[2:])] = value[0]
                payload['max_{}'.format(key[2:])] = value[1]

        recommendations = requests.get(
            SPOTIFY_BASE_URL + '/recommendations',
            headers={
                'Authorization': 'Bearer {}'.format(
                    request.user.spotify_user.get_access_token())
                }, params=payload).json()

        if len(recommendations['tracks']) == 0:
            messages.add_message(
                request,
                messages.WARNING,
                'No tracks found for the selected parameters')
            return redirect('dashboard')

        return render(request, 'recommendations.html', context={
            'recommendations': recommendations
        })
    else:
        spotify_profile = requests.get(SPOTIFY_BASE_URL + '/me', headers={
            'Authorization': 'Bearer {}'.format(
                request.user.spotify_user.get_access_token())
        }).json()

        available_genres = requests.get(
            SPOTIFY_BASE_URL + '/recommendations/available-genre-seeds',
            headers={
                'Authorization': 'Bearer {}'.format(
                    request.user.spotify_user.get_access_token())
                    }).json().get('genres')

        return render(request, 'recommendations_form.html', context={
            'spotify_profile': spotify_profile,
            'available_genres': available_genres
        })


def log_out(request):
    logout(request)
    return redirect('info')
