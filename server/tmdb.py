from flask import current_app
import os
import random
import requests

TMDB_MAX_PAGE = 500


def _fetch_page(endpoint, page):
    resp = requests.get(
        f"{current_app.config['TMDB_BASE']}{endpoint}",
        params={
            'api_key': current_app.config['TMDB_API_KEY'],
            'language': 'en-US',
            'page': page,
        },
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json().get('results', [])


def _results_to_movies(results):
    poster_base = current_app.config['POSTER_BASE']
    movies = []
    for r in results:
        if not r.get('vote_average') or not r.get('poster_path'):
            continue
        movies.append({
            'title': r['title'],
            'year': (r.get('release_date') or '')[:4] or None,
            'rating': round(r['vote_average'], 1),
            'tmdb_id': r['id'],
            'poster_url': f"{poster_base}{r['poster_path']}",
        })
    return movies


def fetch_movies(popular_start=1, top_rated_start=1):
    count = current_app.config['MOVIE_BATCH_SIZE']
    half = count // 2
    endpoints = [
        ('/movie/popular',   popular_start),
        ('/movie/top_rated', top_rated_start),
    ]
    seen_ids = set()
    collected = []
    next_pages = {}

    for endpoint, start_page in endpoints:
        entries_needed = half
        page = start_page
        last_page = start_page

        while entries_needed > 0:
            actual_page = ((page - 1) % TMDB_MAX_PAGE) + 1
            results = _fetch_page(endpoint, actual_page)
            if not results:
                break

            for movie in _results_to_movies(results):
                if movie['tmdb_id'] not in seen_ids:
                    seen_ids.add(movie['tmdb_id'])
                    collected.append(movie)
                    entries_needed -= 1
                    if entries_needed == 0:
                        break

            last_page = actual_page
            page += 1

        next_pages[endpoint] = ((last_page) % TMDB_MAX_PAGE) + 1

    random.shuffle(collected)
    return (
        collected,
        next_pages.get('/movie/popular', popular_start),
        next_pages.get('/movie/top_rated', top_rated_start),
    )