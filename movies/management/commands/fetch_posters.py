import os
import time
import requests

from django.core.management.base import BaseCommand
from movies.models import Movie

TMDB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
TMDB_DETAILS_URL = "https://api.themoviedb.org/3/movie/{id}"


class Command(BaseCommand):
    help = "Fetch poster images from TMDB for movies missing a poster_path"

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=None)
        parser.add_argument(
            '--force',
            action='store_true',
            help='Re-fetch posters even for movies that already have one',
        )

    def handle(self, *args, **options):
        api_key = os.getenv('TMDB_API_KEY')
        if not api_key:
            self.stderr.write(self.style.ERROR(
                "TMDB_API_KEY not found. Add it to your .env file."
            ))
            return

        movies = Movie.objects.all()
        if not options['force']:
            movies = movies.filter(poster_path='')

        if options['limit']:
            movies = movies[:options['limit']]

        total = movies.count()
        self.stdout.write(f"Fetching posters for {total} movies...")

        updated = 0
        not_found = 0

        for i, movie in enumerate(movies, start=1):
            poster_path = None

            try:
                if movie.tmdb_id:
                    resp = requests.get(
                        TMDB_DETAILS_URL.format(id=movie.tmdb_id),
                        params={'api_key': api_key},
                        timeout=10,
                    )
                    if resp.status_code == 200:
                        poster_path = resp.json().get('poster_path')

                if not poster_path:
                    params = {'api_key': api_key, 'query': movie.title}
                    if movie.year:
                        params['year'] = movie.year
                    resp = requests.get(TMDB_SEARCH_URL, params=params, timeout=10)
                    if resp.status_code == 200:
                        results = resp.json().get('results', [])
                        if results:
                            poster_path = results[0].get('poster_path')

            except requests.RequestException as e:
                self.stdout.write(self.style.WARNING(f"  Network error for {movie.title}: {e}"))
                continue

            if poster_path:
                movie.poster_path = poster_path
                movie.save(update_fields=['poster_path'])
                updated += 1
            else:
                not_found += 1

            if i % 50 == 0 or i == total:
                self.stdout.write(f"  Processed {i}/{total}...")

            time.sleep(0.05)

        self.stdout.write(self.style.SUCCESS(
            f"Done. Updated: {updated}, Not found: {not_found}"
        ))