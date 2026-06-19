



import ast
import csv
import os
from datetime import datetime

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from movies.models import Movie, Genre


class Command(BaseCommand):
    help = "Load movies from the TMDB CSV dataset into the database"

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Only import the first N movies (useful for quick testing)',
        )
        parser.add_argument(
            '--movies-csv',
            type=str,
            default='movies/data/tmdb_5000_movies.csv',
            help='Path to the movies CSV file',
        )
        parser.add_argument(
            '--credits-csv',
            type=str,
            default='movies/data/tmdb_5000_credits.csv',
            help='Path to the credits CSV file',
        )

    def handle(self, *args, **options):
        movies_path = options['movies_csv']
        credits_path = options['credits_csv']
        limit = options['limit']

        if not os.path.exists(movies_path):
            self.stderr.write(self.style.ERROR(
                f"Could not find {movies_path}. "
                f"Download the TMDB dataset from Kaggle and place it there."
            ))
            return

        credits_lookup = {}
        if os.path.exists(credits_path):
            with open(credits_path, encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    movie_id = row.get('movie_id')
                    cast_raw = row.get('cast', '[]')
                    crew_raw = row.get('crew', '[]')

                    cast_names = []
                    try:
                        cast_list = ast.literal_eval(cast_raw)
                        cast_names = [c['name'] for c in cast_list[:8]]
                    except (ValueError, SyntaxError):
                        pass

                    director = ''
                    try:
                        crew_list = ast.literal_eval(crew_raw)
                        for member in crew_list:
                            if member.get('job') == 'Director':
                                director = member['name']
                                break
                    except (ValueError, SyntaxError):
                        pass

                    credits_lookup[movie_id] = {
                        'cast': ', '.join(cast_names),
                        'director': director,
                    }
        else:
            self.stdout.write(self.style.WARNING(
                f"Credits file not found at {credits_path} - cast/director will be blank."
            ))

        created_count = 0
        updated_count = 0
        skipped_count = 0

        with open(movies_path, encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            if limit:
                rows = rows[:limit]

            total = len(rows)
            self.stdout.write(f"Importing {total} movies...")

            for i, row in enumerate(rows, start=1):
                tmdb_id = row.get('id')
                title = row.get('title', '').strip()

                if not tmdb_id or not title:
                    skipped_count += 1
                    continue

                genre_names = []
                try:
                    genre_list = ast.literal_eval(row.get('genres', '[]'))
                    genre_names = [g['name'] for g in genre_list]
                except (ValueError, SyntaxError):
                    pass

                keyword_names = []
                try:
                    kw_list = ast.literal_eval(row.get('keywords', '[]'))
                    keyword_names = [k['name'] for k in kw_list]
                except (ValueError, SyntaxError):
                    pass

                release_date = None
                date_str = row.get('release_date', '').strip()
                if date_str:
                    try:
                        release_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                    except ValueError:
                        pass

                def safe_float(val, default=0.0):
                    try:
                        return float(val)
                    except (ValueError, TypeError):
                        return default

                def safe_int(val, default=0):
                    try:
                        return int(float(val))
                    except (ValueError, TypeError):
                        return default

                credit_info = credits_lookup.get(tmdb_id, {'cast': '', 'director': ''})

                movie, created = Movie.objects.update_or_create(
                    tmdb_id=tmdb_id,
                    defaults={
                        'title': title,
                        'overview': row.get('overview', '') or '',
                        'release_date': release_date,
                        'poster_path': '',
                        'vote_average': safe_float(row.get('vote_average')),
                        'vote_count': safe_int(row.get('vote_count')),
                        'popularity': safe_float(row.get('popularity')),
                        'runtime': safe_int(row.get('runtime'), default=None) or None,
                        'language': row.get('original_language', 'en') or 'en',
                        'keywords': ', '.join(keyword_names),
                        'cast': credit_info['cast'],
                        'director': credit_info['director'],
                    }
                )

                genre_objs = []
                for name in genre_names:
                    slug = slugify(name)
                    genre_obj, _ = Genre.objects.get_or_create(
                        name=name, defaults={'slug': slug}
                    )
                    genre_objs.append(genre_obj)
                movie.genres.set(genre_objs)

                if created:
                    created_count += 1
                else:
                    updated_count += 1

                if i % 200 == 0 or i == total:
                    self.stdout.write(f"  Processed {i}/{total}...")

        self.stdout.write(self.style.SUCCESS(
            f"Done. Created: {created_count}, Updated: {updated_count}, Skipped: {skipped_count}"
        ))