from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Genre, Movie, Rating, UserProfile


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ('title', 'release_date', 'vote_average', 'popularity')
    search_fields = ('title', 'director', 'cast')
    list_filter = ('genres', 'language')
    filter_horizontal = ('genres',)


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('user', 'movie', 'score', 'created_at')
    list_filter = ('score',)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user',)