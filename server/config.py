import os

basedir = os.path.abspath(os.path.dirname(__file__))
default_database_location = 'sqlite:///' + os.path.join(basedir, 'app.db')

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL') or default_database_location
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise RuntimeError('SECRET_KEY environment variable is not set')
    
    TMDB_API_KEY = os.environ.get('TMDB_API_KEY')
    if not TMDB_API_KEY:
        raise RuntimeError('TMDB_API_KEY environment variable is not set')

    TMDB_BASE = 'https://api.themoviedb.org/3'
    POSTER_BASE = 'https://image.tmdb.org/t/p/w500'

    MOVIE_BATCH_SIZE = 250
    MOVIE_CACHE_LIMIT = 5000
    REFRESH_DAYS_DELTA = 3