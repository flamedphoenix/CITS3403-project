import json
import random
from flask import request
from flask_login import current_user
from flask_socketio import emit, join_room

from server import db, socketio
from server.models import User, Movie, ChallengeSession

# user_id -> socket session id (tracks online users)
user_sockets = {}

# session_id -> live game state
challenge_states = {}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_random_pairs(num_pairs=10):
    all_movies = Movie.query.all()
    if len(all_movies) < 2:
        return None
    random.shuffle(all_movies)
    pairs, used = [], []
    for movie in all_movies:
        if len(pairs) == num_pairs:
            break
        partner = next(
            (m for m in all_movies if m not in used and m.id != movie.id and m.rating != movie.rating),
            None,
        )
        if partner:
            pairs.append([movie.to_dict(), partner.to_dict()])
            used.extend([movie, partner])
    return pairs if len(pairs) == num_pairs else None


def _speed_bonus(time_taken):
    thresholds = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    bonuses =   [100, 90, 80, 70, 60, 50, 40, 30, 20, 10]
    for t, b in zip(thresholds, bonuses):
        if time_taken < t:
            return b
    return 0


def _resolve_round(session_id):
    state = challenge_states.get(session_id)
    session = ChallengeSession.query.get(session_id)
    if not state or not session:
        return

    pair = state['pairs'][state['round']]
    movie_a, movie_b = pair[0], pair[1]
    correct_choice = 'a' if movie_a['rating'] >= movie_b['rating'] else 'b'

    # Sort players by time_taken so first-correct gets full points
    players_sorted = sorted(
        state['players'].items(),
        key=lambda x: x[1].get('time_taken', 10),
    )

    first_correct_seen = False
    round_results = {}

    for user_id, p in players_sorted:
        is_correct = p['choice'] == correct_choice
        time_taken = p.get('time_taken', 10)

        if is_correct:
            is_first = not first_correct_seen
            base = 100 if is_first else 25
            first_correct_seen = True
            points = base + _speed_bonus(time_taken)
        else:
            is_first = False
            points = 0

        state['players'][user_id]['score'] += points
        if is_correct:
            state['players'][user_id]['correct'] += 1

        round_results[user_id] = {
            'choice': p['choice'],
            'is_correct': is_correct,
            'is_first': is_first,
            'points': points,
            'total_score': state['players'][user_id]['score'],
        }

    room = f'challenge_{session_id}'
    c_id, o_id = session.challenger_id, session.opponent_id

    socketio.emit('round_result', {
        'round': state['round'],
        'correct_choice': correct_choice,
        'movie_a': movie_a,
        'movie_b': movie_b,
        'challenger': {**round_results[c_id], 'user_id': c_id},
        'opponent':   {**round_results[o_id], 'user_id': o_id},
    }, room=room)

    state['round'] += 1

    if state['round'] >= 10:
        _end_game(session_id)
    else:
        for p in state['players'].values():
            p['answered'] = False
            p['choice'] = None
            p['time_taken'] = None


def _end_game(session_id):
    state = challenge_states.get(session_id)
    session = ChallengeSession.query.get(session_id)
    if not state or not session:
        return

    c_id, o_id = session.challenger_id, session.opponent_id
    c_score = state['players'][c_id]['score']
    o_score = state['players'][o_id]['score']

    if c_score > o_score:
        winner_id = c_id
    elif o_score > c_score:
        winner_id = o_id
    else:
        winner_id = None

    session.status = 'completed'
    session.challenger_score = c_score
    session.opponent_score = o_score
    session.winner_id = winner_id
    db.session.commit()

    challenger = User.query.get(c_id)
    opponent = User.query.get(o_id)

    socketio.emit('game_over', {
        'challenger': {
            'user_id': c_id,
            'username': challenger.username,
            'score': c_score,
            'correct': state['players'][c_id]['correct'],
        },
        'opponent': {
            'user_id': o_id,
            'username': opponent.username,
            'score': o_score,
            'correct': state['players'][o_id]['correct'],
        },
        'winner_id': winner_id,
    }, room=f'challenge_{session_id}')

    challenge_states.pop(session_id, None)


# ---------------------------------------------------------------------------
# SocketIO events
# ---------------------------------------------------------------------------

@socketio.on('connect')
def handle_connect():
    if current_user.is_authenticated:
        user_sockets[current_user.id] = request.sid


@socketio.on('disconnect')
def handle_disconnect():
    if current_user.is_authenticated:
        user_sockets.pop(current_user.id, None)


@socketio.on('send_challenge')
def handle_send_challenge(data):
    if not current_user.is_authenticated:
        return

    opponent_id = data.get('opponent_id')
    if not opponent_id or int(opponent_id) == current_user.id:
        emit('challenge_error', {'message': 'Invalid opponent'})
        return

    opponent = User.query.get(int(opponent_id))
    if not opponent:
        emit('challenge_error', {'message': 'User not found'})
        return

    if opponent.id not in user_sockets:
        emit('challenge_error', {'message': f'{opponent.username} is not online right now'})
        return

    session = ChallengeSession(
        challenger_id=current_user.id,
        opponent_id=opponent.id,
        status='pending',
    )
    db.session.add(session)
    db.session.commit()

    emit('challenge_sent', {
        'session_id': session.id,
        'opponent_name': opponent.username,
    })

    socketio.emit('challenge_received', {
        'session_id': session.id,
        'challenger_name': current_user.username,
        'challenger_id': current_user.id,
    }, room=user_sockets[opponent.id])


@socketio.on('accept_challenge')
def handle_accept_challenge(data):
    if not current_user.is_authenticated:
        return

    session_id = int(data.get('session_id'))
    session = ChallengeSession.query.get(session_id)

    if not session or session.opponent_id != current_user.id or session.status != 'pending':
        emit('challenge_error', {'message': 'Challenge no longer available'})
        return

    pairs = _get_random_pairs(10)
    if not pairs:
        emit('challenge_error', {'message': 'Not enough movies in the database'})
        return

    session.status = 'active'
    session.movie_json = json.dumps(pairs)
    db.session.commit()

    challenge_states[session_id] = {
        'pairs': pairs,
        'round': 0,
        'joined': set(),
        'players': {
            session.challenger_id: {'score': 0, 'correct': 0, 'answered': False, 'choice': None, 'time_taken': None},
            session.opponent_id:   {'score': 0, 'correct': 0, 'answered': False, 'choice': None, 'time_taken': None},
        },
    }

    emit('challenge_accepted', {'session_id': session_id})

    challenger_sid = user_sockets.get(session.challenger_id)
    if challenger_sid:
        socketio.emit('challenge_accepted', {'session_id': session_id}, room=challenger_sid)


@socketio.on('decline_challenge')
def handle_decline_challenge(data):
    if not current_user.is_authenticated:
        return

    session_id = int(data.get('session_id'))
    session = ChallengeSession.query.get(session_id)

    if not session or session.opponent_id != current_user.id:
        return

    session.status = 'declined'
    db.session.commit()

    challenger_sid = user_sockets.get(session.challenger_id)
    if challenger_sid:
        socketio.emit('challenge_declined', {
            'opponent_name': current_user.username,
        }, room=challenger_sid)


@socketio.on('join_challenge')
def handle_join_challenge(data):
    if not current_user.is_authenticated:
        return

    session_id = int(data.get('session_id'))
    session = ChallengeSession.query.get(session_id)

    if not session or current_user.id not in [session.challenger_id, session.opponent_id]:
        emit('challenge_error', {'message': 'Invalid session'})
        return

    room = f'challenge_{session_id}'
    join_room(room)

    state = challenge_states.get(session_id)
    if not state:
        emit('challenge_error', {'message': 'Game state not found'})
        return

    state['joined'].add(current_user.id)

    challenger = User.query.get(session.challenger_id)
    opponent = User.query.get(session.opponent_id)

    if len(state['joined']) == 2:
        socketio.emit('game_start', {
            'session_id': session_id,
            'pairs': state['pairs'],
            'challenger': {'user_id': session.challenger_id, 'username': challenger.username},
            'opponent':   {'user_id': session.opponent_id,   'username': opponent.username},
        }, room=room)


@socketio.on('challenge_pick')
def handle_challenge_pick(data):
    if not current_user.is_authenticated:
        return

    session_id = int(data.get('session_id'))
    round_num  = int(data.get('round'))
    choice     = data.get('choice')
    time_taken = float(data.get('time_taken', 10))

    state = challenge_states.get(session_id)
    if not state or state['round'] != round_num:
        return

    player = state['players'].get(current_user.id)
    if not player or player['answered']:
        return

    player['answered']  = True
    player['choice']    = choice
    player['time_taken'] = time_taken

    # Let the other player know their opponent has answered
    session = ChallengeSession.query.get(session_id)
    other_id = session.opponent_id if current_user.id == session.challenger_id else session.challenger_id
    other_sid = user_sockets.get(other_id)
    if other_sid:
        socketio.emit('opponent_answered', {}, room=other_sid)

    if all(p['answered'] for p in state['players'].values()):
        _resolve_round(session_id)


@socketio.on('challenge_timeout')
def handle_challenge_timeout(data):
    if not current_user.is_authenticated:
        return

    session_id = int(data.get('session_id'))
    round_num  = int(data.get('round'))

    state = challenge_states.get(session_id)
    if not state or state['round'] != round_num:
        return

    player = state['players'].get(current_user.id)
    if not player or player['answered']:
        return

    player['answered']  = True
    player['choice']    = None
    player['time_taken'] = 10

    if all(p['answered'] for p in state['players'].values()):
        _resolve_round(session_id)
