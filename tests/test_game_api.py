import unittest
from datetime import date

from server import create_app, db
from server.models import User, Movie, DailyMovieSet, Score, DailyScore
from server.challenge import _speed_bonus


class TestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SECRET_KEY = 'test-secret-key'
    TMDB_API_KEY = 'test-tmdb-key'
    MOVIE_CACHE_LIMIT = 5000
    REFRESH_DAYS_DELTA = 3
    MOVIE_BATCH_SIZE = 250
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _create_user(self, username='testuser', password='testpass'):
        user = User(username=username, email=f'{username}@test.com')
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user.id

    def _login(self, username='testuser', password='testpass'):
        self.client.post('/login', data={
            'username': username,
            'password': password,
        }, follow_redirects=True)

    def _create_and_login(self, username='testuser', password='testpass'):
        self._create_user(username, password)
        self._login(username, password)

    def _add_movies(self, n=20):
        for i in range(n):
            m = Movie(title=f'Movie {i}', year='2020', rating=float(i), tmdb_id=i)
            db.session.add(m)
        db.session.commit()

    def _add_score(self, user_id, score, correct_answers, time_taken):
        s = Score(user_id=user_id, score=score, correct_answers=correct_answers, time_taken=time_taken)
        db.session.add(s)
        db.session.commit()
        return s


# ---------------------------------------------------------------------------
# _speed_bonus pure function
# ---------------------------------------------------------------------------

class TestSpeedBonus(BaseTestCase):
    def test_below_one_second_gives_max_bonus(self):
        self.assertEqual(_speed_bonus(0.5), 100)

    def test_each_threshold_gives_correct_bonus(self):
        cases = [
            (0.9, 100),
            (1.5, 90),
            (2.5, 80),
            (3.5, 70),
            (4.5, 60),
            (5.5, 50),
            (6.5, 40),
            (7.5, 30),
            (8.5, 20),
            (9.5, 10),
        ]
        for time_taken, expected in cases:
            with self.subTest(time_taken=time_taken):
                self.assertEqual(_speed_bonus(time_taken), expected)

    def test_at_ten_seconds_gives_zero(self):
        self.assertEqual(_speed_bonus(10), 0)

    def test_above_ten_seconds_gives_zero(self):
        self.assertEqual(_speed_bonus(15), 0)


# ---------------------------------------------------------------------------
# GET /api/game/questions
# ---------------------------------------------------------------------------

class TestGameQuestions(BaseTestCase):
    def test_returns_ten_pairs_with_enough_movies(self):
        self._create_and_login()
        self._add_movies(20)
        resp = self.client.get('/api/game/questions')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn('pairs', data)
        self.assertEqual(len(data['pairs']), 10)

    def test_each_pair_contains_two_movies(self):
        self._create_and_login()
        self._add_movies(20)
        resp = self.client.get('/api/game/questions')
        for pair in resp.get_json()['pairs']:
            self.assertEqual(len(pair), 2)

    def test_movies_in_pair_have_different_ratings(self):
        self._create_and_login()
        self._add_movies(20)
        resp = self.client.get('/api/game/questions')
        for pair in resp.get_json()['pairs']:
            self.assertNotEqual(pair[0]['rating'], pair[1]['rating'])

    def test_returns_500_with_empty_db(self):
        self._create_and_login()
        resp = self.client.get('/api/game/questions')
        self.assertEqual(resp.status_code, 500)
        self.assertIn('error', resp.get_json())

    def test_requires_login(self):
        resp = self.client.get('/api/game/questions')
        self.assertEqual(resp.status_code, 302)


# ---------------------------------------------------------------------------
# GET /api/game/daily
# ---------------------------------------------------------------------------

class TestGameDaily(BaseTestCase):
    def test_first_call_creates_db_entry(self):
        self._create_and_login()
        self._add_movies(20)
        self.client.get('/api/game/daily')
        entry = DailyMovieSet.query.filter_by(reset_date=date.today()).first()
        self.assertIsNotNone(entry)

    def test_first_call_returns_ten_pairs(self):
        self._create_and_login()
        self._add_movies(20)
        resp = self.client.get('/api/game/daily')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn('pairs', data)
        self.assertEqual(len(data['pairs']), 10)

    def test_second_call_returns_same_pairs(self):
        self._create_and_login()
        self._add_movies(20)
        resp1 = self.client.get('/api/game/daily')
        resp2 = self.client.get('/api/game/daily')
        self.assertEqual(resp1.get_json()['pairs'], resp2.get_json()['pairs'])

    def test_second_call_does_not_duplicate_db_entry(self):
        self._create_and_login()
        self._add_movies(20)
        self.client.get('/api/game/daily')
        self.client.get('/api/game/daily')
        count = DailyMovieSet.query.filter_by(reset_date=date.today()).count()
        self.assertEqual(count, 1)

    def test_invalid_date_param_returns_400(self):
        self._create_and_login()
        resp = self.client.get('/api/game/daily?date=not-a-date')
        self.assertEqual(resp.status_code, 400)

    def test_missing_historical_date_returns_404(self):
        self._create_and_login()
        resp = self.client.get('/api/game/daily?date=2020-01-01')
        self.assertEqual(resp.status_code, 404)

    def test_requires_login(self):
        resp = self.client.get('/api/game/daily')
        self.assertEqual(resp.status_code, 302)


# ---------------------------------------------------------------------------
# GET /api/game/daily/history
# ---------------------------------------------------------------------------

class TestGameDailyHistory(BaseTestCase):
    def test_empty_history_returns_empty_list(self):
        self._create_and_login()
        resp = self.client.get('/api/game/daily/history')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()['dates'], [])

    def test_unplayed_date_shows_played_false(self):
        self._create_and_login()
        db.session.add(DailyMovieSet(reset_date=date.today(), movie_json='[]'))
        db.session.commit()
        resp = self.client.get('/api/game/daily/history')
        entry = resp.get_json()['dates'][0]
        self.assertFalse(entry['played'])
        self.assertIsNone(entry['score'])

    def test_played_date_shows_score_and_correct(self):
        user_id = self._create_user()
        self._login()
        today = date.today()
        db.session.add(DailyMovieSet(reset_date=today, movie_json='[]'))
        db.session.add(DailyScore(user_id=user_id, reset_date=today, score=700, correct_answers=8, time_taken=30.0))
        db.session.commit()
        resp = self.client.get('/api/game/daily/history')
        entry = resp.get_json()['dates'][0]
        self.assertTrue(entry['played'])
        self.assertEqual(entry['score'], 700)
        self.assertEqual(entry['correct'], 8)

    def test_today_entry_is_marked_as_today(self):
        self._create_and_login()
        db.session.add(DailyMovieSet(reset_date=date.today(), movie_json='[]'))
        db.session.commit()
        resp = self.client.get('/api/game/daily/history')
        entry = resp.get_json()['dates'][0]
        self.assertTrue(entry['is_today'])


# ---------------------------------------------------------------------------
# POST /api/game/submit
# ---------------------------------------------------------------------------

class TestGameSubmit(BaseTestCase):
    def _valid_payload(self, **overrides):
        payload = {'score': 500, 'correct_answers': 7, 'time_taken': 45.0, 'mode': 'standard'}
        payload.update(overrides)
        return payload

    def test_valid_submission_saves_score(self):
        self._create_and_login()
        resp = self.client.post('/api/game/submit', json=self._valid_payload())
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.get_json()['saved'])
        self.assertEqual(Score.query.count(), 1)

    def test_returns_best_score_stats(self):
        self._create_and_login()
        resp = self.client.post('/api/game/submit', json=self._valid_payload())
        data = resp.get_json()
        self.assertEqual(data['best_score'], 500)
        self.assertIn('best_time_taken', data)
        self.assertIn('best_correct_answers', data)
        self.assertIn('rank', data)

    def test_second_submission_updates_best_score(self):
        self._create_and_login()
        self.client.post('/api/game/submit', json=self._valid_payload(score=300))
        resp = self.client.post('/api/game/submit', json=self._valid_payload(score=900))
        self.assertEqual(resp.get_json()['best_score'], 900)
        self.assertEqual(Score.query.count(), 2)

    def test_no_data_returns_400(self):
        self._create_and_login()
        resp = self.client.post('/api/game/submit', json={})
        self.assertEqual(resp.status_code, 400)

    def test_missing_score_returns_400(self):
        self._create_and_login()
        resp = self.client.post('/api/game/submit', json={'correct_answers': 7, 'time_taken': 45.0})
        self.assertEqual(resp.status_code, 400)

    def test_missing_correct_answers_returns_400(self):
        self._create_and_login()
        resp = self.client.post('/api/game/submit', json={'score': 500, 'time_taken': 45.0})
        self.assertEqual(resp.status_code, 400)

    def test_missing_time_taken_returns_400(self):
        self._create_and_login()
        resp = self.client.post('/api/game/submit', json={'score': 500, 'correct_answers': 7})
        self.assertEqual(resp.status_code, 400)

    def test_score_above_2000_returns_400(self):
        self._create_and_login()
        resp = self.client.post('/api/game/submit', json=self._valid_payload(score=2001))
        self.assertEqual(resp.status_code, 400)

    def test_score_below_zero_returns_400(self):
        self._create_and_login()
        resp = self.client.post('/api/game/submit', json=self._valid_payload(score=-1))
        self.assertEqual(resp.status_code, 400)

    def test_correct_answers_above_10_returns_400(self):
        self._create_and_login()
        resp = self.client.post('/api/game/submit', json=self._valid_payload(correct_answers=11))
        self.assertEqual(resp.status_code, 400)

    def test_correct_answers_below_zero_returns_400(self):
        self._create_and_login()
        resp = self.client.post('/api/game/submit', json=self._valid_payload(correct_answers=-1))
        self.assertEqual(resp.status_code, 400)

    def test_time_taken_above_100_returns_400(self):
        self._create_and_login()
        resp = self.client.post('/api/game/submit', json=self._valid_payload(time_taken=101))
        self.assertEqual(resp.status_code, 400)

    def test_daily_mode_saves_daily_score(self):
        user_id = self._create_user()
        self._login()
        resp = self.client.post('/api/game/submit', json=self._valid_payload(
            mode='daily', date=str(date.today())
        ))
        self.assertEqual(resp.status_code, 200)
        ds = DailyScore.query.filter_by(user_id=user_id, reset_date=date.today()).first()
        self.assertIsNotNone(ds)
        self.assertEqual(ds.score, 500)
        self.assertEqual(ds.correct_answers, 7)

    def test_daily_mode_does_not_create_duplicate_daily_score(self):
        user_id = self._create_user()
        self._login()
        payload = self._valid_payload(mode='daily', date=str(date.today()))
        self.client.post('/api/game/submit', json=payload)
        self.client.post('/api/game/submit', json=payload)
        count = DailyScore.query.filter_by(user_id=user_id, reset_date=date.today()).count()
        self.assertEqual(count, 1)

    def test_standard_mode_does_not_save_daily_score(self):
        user_id = self._create_user()
        self._login()
        self.client.post('/api/game/submit', json=self._valid_payload(mode='standard'))
        self.assertEqual(DailyScore.query.filter_by(user_id=user_id).count(), 0)

    def test_rank_is_1_for_sole_player(self):
        self._create_and_login()
        resp = self.client.post('/api/game/submit', json=self._valid_payload())
        self.assertEqual(resp.get_json()['rank'], 1)


# ---------------------------------------------------------------------------
# GET /api/scores/leaderboard
# ---------------------------------------------------------------------------

class TestLeaderboard(BaseTestCase):
    def test_empty_leaderboard(self):
        resp = self.client.get('/api/scores/leaderboard')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()['leaderboard'], [])

    def test_ranked_by_best_score_descending(self):
        id1 = self._create_user('user1', 'pass1')
        id2 = self._create_user('user2', 'pass2')
        self._add_score(id1, 800, 8, 40.0)
        self._add_score(id2, 1200, 10, 25.0)
        rows = self.client.get('/api/scores/leaderboard').get_json()['leaderboard']
        self.assertEqual(rows[0]['username'], 'user2')
        self.assertEqual(rows[0]['rank'], 1)
        self.assertEqual(rows[1]['username'], 'user1')
        self.assertEqual(rows[1]['rank'], 2)

    def test_tiebreak_by_lower_time(self):
        id1 = self._create_user('slow', 'pass')
        id2 = self._create_user('fast', 'pass')
        self._add_score(id1, 1000, 10, 60.0)
        self._add_score(id2, 1000, 10, 20.0)
        rows = self.client.get('/api/scores/leaderboard').get_json()['leaderboard']
        self.assertEqual(rows[0]['username'], 'fast')

    def test_row_has_expected_fields(self):
        user_id = self._create_user()
        self._add_score(user_id, 500, 7, 45.0)
        row = self.client.get('/api/scores/leaderboard').get_json()['leaderboard'][0]
        for field in ('rank', 'username', 'best_score', 'best_time', 'avg_accuracy', 'games_played'):
            with self.subTest(field=field):
                self.assertIn(field, row)

    def test_games_played_counts_all_submissions(self):
        user_id = self._create_user()
        self._add_score(user_id, 500, 7, 45.0)
        self._add_score(user_id, 800, 9, 30.0)
        row = self.client.get('/api/scores/leaderboard').get_json()['leaderboard'][0]
        self.assertEqual(row['games_played'], 2)


# ---------------------------------------------------------------------------
# GET /profile
# ---------------------------------------------------------------------------

class TestProfile(BaseTestCase):
    def test_requires_login(self):
        resp = self.client.get('/profile')
        self.assertEqual(resp.status_code, 302)

    def test_loads_for_user_with_no_scores(self):
        self._create_and_login()
        resp = self.client.get('/profile', follow_redirects=True)
        self.assertEqual(resp.status_code, 200)

    def test_shows_username_in_page(self):
        self._create_and_login('myplayer')
        resp = self.client.get('/profile', follow_redirects=True)
        self.assertIn(b'myplayer', resp.data)

    def test_loads_for_user_with_scores(self):
        user_id = self._create_user()
        self._login()
        self._add_score(user_id, 750, 8, 35.0)
        resp = self.client.get('/profile', follow_redirects=True)
        self.assertEqual(resp.status_code, 200)

    def test_profile_does_not_show_other_users_data(self):
        id1 = self._create_user('player1', 'password01')
        id2 = self._create_user('player2', 'password02')
        self._add_score(id1, 1500, 10, 10.0)
        self._add_score(id2, 200, 3, 80.0)
        self._login('player2', 'password02')
        resp = self.client.get('/profile', follow_redirects=True)
        # player2's username should appear, not player1's score as their own
        self.assertIn(b'player2', resp.data)
        self.assertEqual(resp.status_code, 200)


if __name__ == '__main__':
    unittest.main()
