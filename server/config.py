import os

basedir = os.path.abspath(os.path.dirname(__file__))
default_database_location = 'sqlite:///' + os.path.join(basedir, 'app.db')

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL') or default_database_location
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-later'

    TMDB_API_KEY = os.environ.get('TMDB_API_KEY')
    TMDB_BASE = 'https://api.themoviedb.org/3'
    POSTER_BASE = 'https://image.tmdb.org/t/p/w500'
