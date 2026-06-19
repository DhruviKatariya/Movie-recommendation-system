import os
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from django.conf import settings


ML_MODELS_DIR = getattr(settings, 'ML_MODELS_DIR', Path('ml_models'))


class ContentBasedEngine:
    def __init__(self):
        self.tfidf_matrix = None
        self.movie_indices = None
        self.movies_df = None
        self._load_or_build()

    def _build_soup(self, movie):
        parts = []
        genres = ' '.join(movie.genres.values_list('name', flat=True))
        parts.append(genres * 3)
        if movie.keywords:
            parts.append(movie.keywords.replace(',', ' '))
        if movie.cast:
            cast_names = ' '.join(movie.cast.split(',')[:5])
            parts.append(cast_names)
        if movie.director:
            parts.append(movie.director * 2)
        if movie.overview:
            parts.append(movie.overview)
        return ' '.join(parts).lower()

    def build(self):
        from movies.models import Movie
        movies = Movie.objects.prefetch_related('genres').all()

        data = []
        for m in movies:
            data.append({
                'id': m.id,
                'title': m.title,
                'soup': self._build_soup(m),
            })

        if not data:
            return False

        self.movies_df = pd.DataFrame(data)
        self.movie_indices = pd.Series(
            self.movies_df.index, index=self.movies_df['id']
        )

        vectorizer = TfidfVectorizer(
            stop_words='english',
            ngram_range=(1, 2),
            max_features=10000,
        )
        self.tfidf_matrix = vectorizer.fit_transform(self.movies_df['soup'])

        os.makedirs(ML_MODELS_DIR, exist_ok=True)
        joblib.dump(self.tfidf_matrix, ML_MODELS_DIR / 'tfidf_matrix.pkl')
        joblib.dump(self.movie_indices, ML_MODELS_DIR / 'movie_indices.pkl')
        joblib.dump(self.movies_df, ML_MODELS_DIR / 'movies_df.pkl')
        return True

    def _load_or_build(self):
        paths = [
            ML_MODELS_DIR / 'tfidf_matrix.pkl',
            ML_MODELS_DIR / 'movie_indices.pkl',
            ML_MODELS_DIR / 'movies_df.pkl',
        ]
        if all(p.exists() for p in paths):
            try:
                self.tfidf_matrix = joblib.load(ML_MODELS_DIR / 'tfidf_matrix.pkl')
                self.movie_indices = joblib.load(ML_MODELS_DIR / 'movie_indices.pkl')
                self.movies_df = joblib.load(ML_MODELS_DIR / 'movies_df.pkl')
                return
            except Exception:
                pass
        try:
            self.build()
        except Exception:
            pass

    def get_similar(self, movie_id, n=10):
        if self.tfidf_matrix is None or movie_id not in self.movie_indices:
            return []

        idx = self.movie_indices[movie_id]
        movie_vec = self.tfidf_matrix[idx]
        sim_scores = cosine_similarity(movie_vec, self.tfidf_matrix).flatten()
        sim_scores[idx] = 0

        top_indices = np.argsort(sim_scores)[::-1][:n]
        results = []
        for i in top_indices:
            mid = int(self.movies_df.iloc[i]['id'])
            results.append((mid, float(sim_scores[i])))
        return results


class RecommendationEngine:
    def __init__(self):
        self.content_engine = ContentBasedEngine()

    def get_similar_movies(self, movie_id, n=10):
        from movies.models import Movie
        similar_ids_scores = self.content_engine.get_similar(movie_id, n=n)

        if not similar_ids_scores:
            try:
                target = Movie.objects.get(pk=movie_id)
                genre_ids = target.genres.values_list('id', flat=True)
                return list(
                    Movie.objects.filter(genres__in=genre_ids)
                    .exclude(pk=movie_id)
                    .distinct()
                    .order_by('-popularity')[:n]
                )
            except Movie.DoesNotExist:
                return []

        movie_ids = [mid for mid, _ in similar_ids_scores]
        movies = Movie.objects.filter(pk__in=movie_ids)
        movie_map = {m.id: m for m in movies}
        return [movie_map[mid] for mid in movie_ids if mid in movie_map]

    def get_recommendations(self, user_id, n=12):
        from movies.models import Movie, Rating

        user_ratings = Rating.objects.filter(user_id=user_id).select_related('movie')
        if not user_ratings.exists():
            return list(Movie.objects.order_by('-popularity')[:n])

        rated_ids = set(r.movie_id for r in user_ratings)
        liked = [r.movie_id for r in user_ratings.order_by('-score')[:5]]

        content_scores = {}
        for liked_id in liked:
            similar = self.content_engine.get_similar(liked_id, n=20)
            for mid, sim in similar:
                if mid not in rated_ids:
                    content_scores[mid] = content_scores.get(mid, 0) + sim

        if not content_scores:
            return list(
                Movie.objects.exclude(pk__in=rated_ids).order_by('-popularity')[:n]
            )

        top_ids = sorted(content_scores, key=content_scores.get, reverse=True)[:n]
        movies = Movie.objects.filter(pk__in=top_ids)
        movie_map = {m.id: m for m in movies}
        return [movie_map[mid] for mid in top_ids if mid in movie_map]