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

