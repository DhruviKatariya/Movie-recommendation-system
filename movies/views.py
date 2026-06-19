from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Movie, Rating, Genre
from recommendations.engine import RecommendationEngine


def home(request):
    trending = Movie.objects.order_by('-popularity')[:12]
    top_rated = Movie.objects.filter(vote_count__gte=100).order_by('-vote_average')[:8]
    genres = Genre.objects.all()

    recommendations = []
    if request.user.is_authenticated:
        engine = RecommendationEngine()
        recommendations = engine.get_recommendations(request.user.id, n=8)

    return render(request, 'movies/home.html', {
        'trending': trending,
        'top_rated': top_rated,
        'genres': genres,
        'recommendations': recommendations,
    })


def movie_list(request):
    movies = Movie.objects.all()
    query = request.GET.get('q', '')
    genre_slug = request.GET.get('genre', '')
    sort = request.GET.get('sort', '-popularity')

    if query:
        movies = movies.filter(
            Q(title__icontains=query) |
            Q(overview__icontains=query) |
            Q(cast__icontains=query) |
            Q(director__icontains=query)
        )

    if genre_slug:
        movies = movies.filter(genres__slug=genre_slug)

    valid_sorts = ['-popularity', '-vote_average', '-release_date', 'title']
    if sort in valid_sorts:
        movies = movies.order_by(sort)

    genres = Genre.objects.all()
    return render(request, 'movies/list.html', {
        'movies': movies[:60],
        'genres': genres,
        'query': query,
        'current_genre': genre_slug,
        'current_sort': sort,
    })


def movie_detail(request, pk):
    movie = get_object_or_404(Movie, pk=pk)
    user_rating = None

    if request.user.is_authenticated:
        user_rating = Rating.objects.filter(
            user=request.user, movie=movie
        ).first()

    engine = RecommendationEngine()
    similar = engine.get_similar_movies(movie.id, n=6)
    recent_reviews = movie.ratings.select_related('user').exclude(review='')[:5]

    return render(request, 'movies/detail.html', {
        'movie': movie,
        'user_rating': user_rating,
        'similar': similar,
        'recent_reviews': recent_reviews,
    })


@login_required
def rate_movie(request, pk):
    movie = get_object_or_404(Movie, pk=pk)
    if request.method == 'POST':
        score = float(request.POST.get('score', 0))
        review = request.POST.get('review', '').strip()

        if 0.5 <= score <= 5.0:
            Rating.objects.update_or_create(
                user=request.user,
                movie=movie,
                defaults={'score': score, 'review': review}
            )
            messages.success(request, f'Your rating for "{movie.title}" has been saved.')
        else:
            messages.error(request, 'Please provide a valid score between 0.5 and 5.')

    return redirect('movie_detail', pk=pk)


@login_required
def watchlist(request):
    user_ratings = Rating.objects.filter(
        user=request.user
    ).select_related('movie').order_by('-created_at')

    return render(request, 'movies/watchlist.html', {
        'user_ratings': user_ratings,
    })