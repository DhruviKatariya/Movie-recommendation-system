from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('movies/', views.movie_list, name='movie_list'),
    path('movies/<int:pk>/', views.movie_detail, name='movie_detail'),
    path('movies/<int:pk>/rate/', views.rate_movie, name='rate_movie'),
    path('watchlist/', views.watchlist, name='watchlist'),
]