from flask import Blueprint, render_template, redirect, url_for, flash, jsonify, request, current_app
from flask_login import login_user, current_user, logout_user, login_required
from server.forms import LoginForm, RegistrationForm
from server.models import User, Movie, Score, SystemState, DailyMovieSet
from server.tmdb import fetch_movies
from datetime import date, datetime, timezone, timedelta
from server import db
import random, json


main = Blueprint('main', __name__)


@main.route('/')
def index():
    return render_template('index.html')


@main.route('/game')
@login_required
def game():
    return render_template('game.html')


@main.route('/scoreboard')
def scoreboard():
    return render_template('scoreboard.html')


@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('main.login'))
        login_user(user, remember=form.remember_me.data)
        flash(f'Successfully logged in as {form.username.data}')
        return redirect(url_for('main.index'))
    return render_template('login.html', form=form)


@main.route('/register', methods=['GET', 'POST']) 
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(username=form.username.data).first()
        existing_email = User.query.filter_by(email=form.email.data).first()

        if existing_user and existing_email:
            flash('Username and email are already in use')
            return redirect(url_for('main.register'))

        if existing_user:
            flash('Username already taken')
            return redirect(url_for('main.register'))

        if existing_email:
            flash('Email already registered')
            return redirect(url_for('main.register'))
        
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        
        flash(f'Registration requested for user {form.username.data}')
        return redirect(url_for('main.index'))
    return render_template('register.html', form=form)


@main.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))

def get_random_movie_batch(num_pairs=10):
    all_movies = Movie.query.all()
    if len(all_movies) < 2:
        return None
    
    random.shuffle(all_movies)
    pairs = []
    used = []

    for movie in all_movies:
        if len(pairs) == num_pairs:
            break
        partner = next(
            (m for m in all_movies if m not in used and m.id != movie.id and m.rating != movie.rating),
            None
        )
        if partner:
            pairs.append([movie.to_dict(), partner.to_dict()])
            used.extend([movie, partner])
    return pairs if len(pairs) == num_pairs else None
        return jsonify({'error': 'Not enough movies with distinct ratings'}), 500

    return jsonify({'pairs': pairs})


@main.route('/api/game/submit', methods=['POST'])
@login_required
def game_submit():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    score_value = data.get('score')
    correct_answers = data.get('correct_answers')
    time_taken = data.get('time_taken')

    if any(v is None for v in [score_value, correct_answers, time_taken]):
        return jsonify({'error': 'Missing fields'}), 400

    score = Score(
        user_id=current_user.id,
        score=score_value,
        correct_answers=correct_answers,
        time_taken=time_taken,
    )
    db.session.add(score)
    db.session.commit()

    best = Score.query.filter_by(user_id=current_user.id).order_by(Score.score.desc()).first()

    user_best_subq = db.session.query(
        db.func.max(Score.score)
    ).filter(Score.user_id == User.id).correlate(User).scalar_subquery()

    rank = db.session.query(db.func.count()).filter(
        user_best_subq > best.score
    ).scalar() + 1

    return jsonify({'saved': True, 'best_score': best.score, 'rank': rank})


@main.route('/api/scores/leaderboard')
def leaderboard():
    best_scores = db.session.query(
        User.username,
        db.func.max(Score.score).label('best_score'),
        db.func.min(Score.time_taken).label('best_time'),
        db.func.count(Score.id).label('games_played'),
        db.func.round(
            db.func.avg(Score.correct_answers) * 10, 1
        ).label('avg_accuracy'),
    ).join(Score, User.id == Score.user_id).group_by(User.id).order_by(
        db.text('best_score DESC')
    ).limit(50).all()

    return jsonify({'leaderboard': [
        {
            'rank': i + 1,
            'username': row.username,
            'best_score': row.best_score,
            'best_time': row.best_time,
            'games_played': row.games_played,
            'avg_accuracy': f'{row.avg_accuracy}%',
        }
        for i, row in enumerate(best_scores)
    ]})


def maintain_movie_cache():
    max_cache = current_app.config['MOVIE_CACHE_LIMIT']
    refresh_delta = current_app.config['REFRESH_DAYS_DELTA']

    current_count = Movie.query.count()
    if current_count >= max_cache:
        return
    
    state = SystemState.query.first()
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    if not state:
        state = SystemState(last_refresh=now - timedelta(days=refresh_delta))
        db.session.add(state)
        db.session.commit()

    if now - state.last_refresh > timedelta(days=refresh_delta) or current_count < 30:
        new_data, next_pop, next_top = fetch_movies(state.next_popular_page, state.next_top_rated_page)

        for m_data in new_data:
            if not Movie.query.filter_by(tmdb_id=m_data['tmdb_id']).first():
                db.session.add(Movie(**m_data))
        
        state.last_refresh = now
        state.next_popular_page = next_pop
        state.next_top_rated_page = next_top
        db.session.commit()
    