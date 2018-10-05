from django.urls import path, include

from app import views
from app.tasks import update_play_history

urlpatterns = [
    path('admin/', include('admin.urls')),
    path('', views.info, name='info'),
    path('authorize/', views.authorize, name='authorize'),
    path('authenticate/', views.authenticate, name='authenticate'),
    path('delete_user/', views.delete_user, name='delete_user'),
    path('update_archive/',views.update_archive, name='update_archive'),
    path('about/',views.about, name='about'),
    path('spotify_authorize/', views.spotify_authorize, name='spotify_authorize'),
    path('spotify_authenticate/', views.spotify_authenticate, name='spotify_authenticate'),
    path('spotify_delink/', views.spotify_delink, name='spotify_delink'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('debug/', update_play_history),
    path('recommendations/', views.recommendations, name='recommendations'),
    path('logout/', views.log_out, name='logout')
]
