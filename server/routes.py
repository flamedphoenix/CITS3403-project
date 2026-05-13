from flask import Blueprint, render_template, redirect, url_for, flash, jsonify, request, current_app
from flask_login import login_user, current_user, logout_user, login_required
from server.forms import LoginForm, RegistrationForm
from server.models import User, Movie, Score, SystemState, DailyMovieSet, DailyScore
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
    best_scores = []

    users = User.query.join(Score).all()

    for user in users:
        best_score = Score.query.filter_by(user_id=user.id).order_by(
            Score.score.desc(),
            Score.time_taken.asc(),
            Score.correct_answers.desc()
        ).first()

        if best_score:
            best_scores.append({
                'username': user.username,
                'score': best_score.score,
                'time_taken': best_score.time_taken,
                'correct_answers': best_score.correct_answers,
                'accuracy': round((best_score.correct_answers / 10) * 100),
            })

    best_scores.sort(key=lambda row: (-row['score'], row['time_taken'], -row['correct_answers']))

    for index, row in enumerate(best_scores, start=1):
        row['rank'] = index

    user_stats = None

    if current_user.is_authenticated:
        for row in best_scores:
            if row['username'] == current_user.username:
                user_stats = row
                break

    return render_template(
        'scoreboard.html',
        leaderboard=best_scores,
        user_stats=user_stats
    )



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
        if existing_user or existing_email:
            flash('An account with those details already exists')
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
@login_required
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


@main.route('/api/game/questions')
@login_required
def game_questions():
    pairs = get_random_movie_batch(10)
    if not pairs:
        return jsonify({'error': 'Not enough movies with distinct ratings'}), 500
    return jsonify({'pairs': pairs})

@main.route('/api/admin/maintain-cache')
@login_required
def trigger_maintenance():
    maintain_movie_cache()
    return jsonify({'status': 'ok'})


@main.route('/api/game/daily')
@login_required
def game_daily():
    date_param = request.args.get('date', default=None, type=str)
    if date_param:
        try:
            target_date = date.fromisoformat(date_param)
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400
        
        daily_entry = DailyMovieSet.query.filter_by(reset_date=target_date).first()
        if not daily_entry:
            return jsonify({'error': f'No daily game exists for {date_param}'}), 404
        return jsonify({'pairs': json.loads(daily_entry.movie_json), 'date': date_param})

    target_date = date.today()
    daily_entry = DailyMovieSet.query.filter_by(reset_date=target_date).first()

    if not daily_entry:
        pairs = get_random_movie_batch(10)
        if not pairs:
            return jsonify({'error': 'Database too small for daily mode'}), 500

        new_set = DailyMovieSet(reset_date=target_date, movie_json=json.dumps(pairs))
        db.session.add(new_set)
        db.session.commit()
        return jsonify({'pairs': pairs})
    
    return jsonify({'pairs': json.loads(daily_entry.movie_json), 'today_date': str(target_date)})



@main.route('/api/game/daily/history')
@login_required
def game_daily_history():
    entries = DailyMovieSet.query.order_by(DailyMovieSet.reset_date.desc()).limit(30).all()
    today = date.today()

    user_daily_scores = {
        ds.reset_date: ds
        for ds in DailyScore.query.filter_by(user_id=current_user.id).all()
    }

    return jsonify({
        'dates': [
            {
                'date': str(e.reset_date),
                'is_today': e.reset_date == today,
                'label': e.reset_date.strftime('%b %d, %Y'),
                'played': e.reset_date in user_daily_scores,
                'score': user_daily_scores[e.reset_date].score if e.reset_date in user_daily_scores else None,
                'correct': user_daily_scores[e.reset_date].correct_answers if e.reset_date in user_daily_scores else None,
            }
            for e in entries
        ]
    })



@main.route('/api/game/submit', methods=['POST'])
@login_required
def game_submit():
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    score_value = data.get('score')
    correct_answers = data.get('correct_answers')
    time_taken = data.get('time_taken')
    mode = data.get('mode', 'standard')
    game_date = data.get('date')


    if any(v is None for v in [score_value, correct_answers, time_taken]):
        return jsonify({'error': 'Missing fields'}), 400

    try:
        score_value = int(score_value)
        correct_answers = int(correct_answers)
        time_taken = float(time_taken)
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid data types'}), 400

    if not (0 <= score_value <= 2000): return jsonify({'error': 'Score out of valid range'}), 400
    if not (0 <= correct_answers <= 10): return jsonify({'error': 'correct_answers out of valid range'}), 400
    if not (0 <= time_taken <= 100): return jsonify({'error': 'time_taken out of valid range'}), 400

    new_score = Score(
        user_id=current_user.id,
        score=score_value,
        correct_answers=correct_answers,
        time_taken=round(time_taken, 1),
    )

    db.session.add(new_score)
    if mode == 'daily' and game_date is not None:
        try:
            played_date = date.fromisoformat(game_date)

            if played_date == date.today():
                already_saved = DailyScore.query.filter_by(
                    user_id=current_user.id,
                    reset_date=played_date
                ).first()
                
                if not already_saved:
                    daily_score = DailyScore(
                        user_id=current_user.id,
                        reset_date=played_date,
                        score=score_value,
                        correct_answers=correct_answers,
                        time_taken=round(time_taken, 1),
                    )
                    db.session.add(daily_score)
        except ValueError:
            pass

    db.session.commit()

    best_score = Score.query.filter_by(user_id=current_user.id).order_by(
        Score.score.desc(),
        Score.time_taken.asc(),
        Score.correct_answers.desc()
    ).first()

    all_best_scores = []

    for user in User.query.join(Score).all():
        user_best = Score.query.filter_by(user_id=user.id).order_by(
            Score.score.desc(),
            Score.time_taken.asc(),
            Score.correct_answers.desc()
        ).first()

        if user_best:
            all_best_scores.append(user_best)

    all_best_scores.sort(key=lambda s: (-s.score, s.time_taken, -s.correct_answers))

    rank = next(
        (index + 1 for index, score in enumerate(all_best_scores) if score.user_id == current_user.id),
        None
    )

    return jsonify({
        'saved': True,
        'best_score': best_score.score,
        'best_time_taken': best_score.time_taken,
        'best_correct_answers': best_score.correct_answers,
        'best_accuracy': round((best_score.correct_answers / 10) * 100),
        'rank': rank
    })


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

    today = date.today()
    last_refresh_date = state.last_refresh.date()
    days_since_refresh = (today - last_refresh_date).days

    if days_since_refresh >= refresh_delta or current_count < 30:
        new_data, next_pop, next_top = fetch_movies(state.next_popular_page, state.next_top_rated_page)

        for m_data in new_data:
            if not Movie.query.filter_by(tmdb_id=m_data['tmdb_id']).first():
                db.session.add(Movie(**m_data))
        
        state.last_refresh = now
        state.next_popular_page = next_pop
        state.next_top_rated_page = next_top
        db.session.commit()
    