# Movie-recommendation-system
recommendation system

CineMatch — Movie Recommendation System

A Django web application that recommends movies using machine learning. It combines a content-based filtering engine (TF-IDF + cosine similarity) with TMDB movie data to suggest similar titles and personalized picks.

Features


Browse, search, and filter 4,800+ movies by genre, rating, or release date
View movie details: overview, cast, director, genres, TMDB rating
Rate movies (0.5–5 stars) and write short reviews
"Similar movies" recommendations on every movie detail page
Personalized "Recommended for you" section based on your ratings
Movie posters fetched live from the TMDB API
Django admin panel for managing the movie catalog


Tech stack

LayerTechnologyBackendDjango 4.2+DatabaseSQLite (default), swappable for PostgreSQLMachine learningscikit-learn (TF-IDF, cosine similarity), pandas, numpyModel cachingjoblibFrontendDjango templates, Bootstrap 5External dataTMDB dataset (Kaggle) + TMDB API for postersAuthDjango's built-in django.contrib.auth

How the recommendation engine works

Each movie is converted into a "soup" of text combining its genres, keywords, top cast, director, and overview. TfidfVectorizer turns every movie's soup into a numerical vector, and cosine_similarity measures how close two movies are in that vector space. The trained matrix is cached to disk with joblib so it only needs to be rebuilt when the dataset changes.


Similar movies (on a detail page) — nearest neighbors to the current movie by cosine similarity.
Personalized recommendations (on the homepage) — built from the user's highest-rated movies, blending the similar-movie results for each one.
Cold start — users with no ratings yet see trending/popular movies instead.


Project structure

## Project structure

\```
movie_recommender/
├── manage.py
├── requirements.txt
├── .env                        # TMDB_API_KEY (not committed)
├── config/
│   ├── settings.py
│   └── urls.py
├── movies/
│   ├── models.py                # Movie, Genre, Rating, UserProfile
│   ├── views.py                 # home, movie_list, movie_detail, rate_movie, watchlist
│   ├── urls.py
│   ├── admin.py
│   ├── data/                    # TMDB CSV files go here
│   └── management/commands/
│       ├── load_movies.py       # imports the TMDB CSV into the database
│       └── fetch_posters.py     # fetches poster_path from the TMDB API
├── recommendations/
│   └── engine.py                # ContentBasedEngine, RecommendationEngine
├── templates/
│   ├── base.html
│   └── movies/
│       ├── home.html
│       ├── list.html
│       ├── detail.html
│       └── watchlist.html
└── ml_models/                   # cached .pkl files (auto-generated, not committed)
\```
Setup

1. Clone and create a virtual environment

bashpython -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

2. Install dependencies

bashpip install -r requirements.txt

3. Configure environment variables

Create a .env file in the project root:

TMDB_API_KEY=your_tmdb_api_key_here

Get a free key at themoviedb.org → Settings → API.

4. Run migrations

bashpython manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser

5. Load movie data

Download the TMDB 5000 Movie Dataset from Kaggle and place both CSVs in movies/data/:

movies/data/tmdb_5000_movies.csv
movies/data/tmdb_5000_credits.csv

Then import:

bashpython manage.py load_movies

6. Fetch movie posters

bashpython manage.py fetch_posters

7. Run the server

bashpython manage.py runserver

Visit http://127.0.0.1:8000.

Management commands

CommandPurposeload_movies --limit NImport movies from the TMDB CSV (optionally limit count)fetch_posters --limit N --forceFetch poster images from TMDB (--force re-fetches existing)

Roadmap / possible extensions


Collaborative filtering with scikit-surprise (SVD) blended with content-based scores
REST API via Django REST Framework for a separate frontend
User watchlists and "mark as watched"
Dockerized deployment with PostgreSQL


License

This project uses the TMDB dataset and API but is not endorsed or certified by TMDB.