from django.urls import path, include

from app import views

urlpatterns = [
    path('admin/', include('admin.urls')),
    path('', views.info, name='info'),
    path('authorize/', views.authorize, name='authorize'),
    path('authenticate/', views.authenticate, name='authenticate'),
    path('delete_user/', views.delete_user, name='delete_user'),
    path('update_archive/', views.update_archive, name='update_archive'),
    path('about/', views.about, name='about'),
    path('oura_authorize/', views.oura_authorize, name='oura_authorize'),
    path('oura_authenticate/', views.oura_authenticate, name='oura_authenticate'),
    path('oura_delink/', views.oura_delink, name='oura_delink'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('logout/', views.log_out, name='logout')
]
