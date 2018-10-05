import os
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.shortcuts import render, redirect

from app.decorators import admin_required


def log_in(request):
    if request.method == 'POST':
        if request.POST.get('admin_password') == os.getenv('ADMIN_PASSWORD'):
            login(request, User.objects.get(username='admin'))
            return redirect('admin_config')
        else:
            messages.error(request, 'Incorrect password')
            return redirect('admin_login')

    return render(request, 'admin_login.html')


@admin_required
def config(request):
    return render(request, 'admin_config.html')
