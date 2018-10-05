from django.urls import path

from admin import views

urlpatterns = [
    path('login/', views.log_in, name='admin_login'),
    path('config/', views.config, name='admin_config'),
]
