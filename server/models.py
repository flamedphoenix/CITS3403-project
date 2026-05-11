from datetime import datetime, timezone
from server import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    scores = db.relationship('Score', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    year = db.Column(db.String(4))
    rating = db.Column(db.Float, nullable=False)
    tmdb_id = db.Column(db.Integer, unique=True)
    poster_url = db.Column(db.String(300))

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'year': self.year,
            'rating': self.rating,
            'poster_url': self.poster_url,
        }

    def __repr__(self):
        return f'<Movie {self.title} ({self.rating})>'
    
    
class DailyMovieSet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reset_date = db.Column(db.Date, unique=True, nullable=False, index=True)
    movie_json = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f'<DailyMovieSet {self.reset_date}>'


class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    correct_answers = db.Column(db.Integer, nullable=False)
    time_taken = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<Score {self.score} by user {self.user_id}>'


class SystemState(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    last_refresh = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    next_popular_page = db.Column(db.Integer, default=1)
    next_top_rated_page = db.Column(db.Integer, default=1)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))