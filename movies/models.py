

# Create your models here.
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Movie(models.Model):
    tmdb_id = models.IntegerField(unique=True, null=True, blank=True)
    title = models.CharField(max_length=300)
    overview = models.TextField(blank=True)
    release_date = models.DateField(null=True, blank=True)
    genres = models.ManyToManyField(Genre, blank=True)
    poster_path = models.CharField(max_length=255, blank=True)
    backdrop_path = models.CharField(max_length=255, blank=True)
    vote_average = models.FloatField(default=0.0)
    vote_count = models.IntegerField(default=0)
    popularity = models.FloatField(default=0.0)
    runtime = models.IntegerField(null=True, blank=True)
    language = models.CharField(max_length=10, default='en')
    keywords = models.TextField(blank=True)
    cast = models.TextField(blank=True)
    director = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    @property
    def poster_url(self):
        if self.poster_path:
            return f"https://image.tmdb.org/t/p/w500{self.poster_path}"
        return "/static/img/no-poster.png"

    @property
    def year(self):
        return self.release_date.year if self.release_date else None

    @property
    def avg_user_rating(self):
        ratings = self.ratings.all()
        if ratings:
            return round(sum(r.score for r in ratings) / len(ratings), 1)
        return None

    class Meta:
        ordering = ['-popularity']


class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ratings')
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='ratings')
    score = models.FloatField(
        validators=[MinValueValidator(0.5), MaxValueValidator(5.0)]
    )
    review = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'movie')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} rated {self.movie.title}: {self.score}"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True)
    favorite_genres = models.ManyToManyField(Genre, blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)

    def __str__(self):
        return f"Profile: {self.user.username}"