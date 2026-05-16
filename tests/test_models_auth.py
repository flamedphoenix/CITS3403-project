import unittest
from datetime import date, datetime, timezone
from server import create_app, db
from server.models import User, Score, DailyScore, ChallengeSession

class TestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = False
    SECRET_KEY = 'testing-secret-key'

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

    def _create_user(self, username='tester', email='test@example.com', password='Password123'):
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user.id

    def _login(self, username='tester', password='Password123'):
        return self.client.post('/login', data={
            'username': username, 'password': password
        }, follow_redirects=True)
    

    def _create_and_login(self, username='testuser', password='testpass123'):
        self._create_user(username, password)
        self._login(username, password)

    def _create_score(self, user_id, score=500, correct_answers=5, time_taken=30.0):
        new_score = Score(user_id=user_id, score=score, correct_answers=correct_answers, time_taken=time_taken)
        db.session.add(new_score)
        db.session.commit()
        return new_score.id
    
    def _create_daily_score(self, user_id, score=100, correct_answers=3, time_taken=20.0, reset_date=None):
        daily_score = DailyScore(user_id=user_id, score=score, correct_answers=correct_answers, time_taken=time_taken, reset_date=reset_date or date.today())
        db.session.add(daily_score)
        db.session.commit()
        return daily_score.id


# ---------------------------------------------------------------------------
# User model: password hashing, fields, uniqueness
# ---------------------------------------------------------------------------
class TestUserModel(BaseTestCase):
    def test_password_hashing(self):
        user = User(username='alice', email='alice@test.com')
        user.set_password('mysecretpass')
        self.assertNotEqual(user.password_hash, 'mysecretpass')
        self.assertIsNotNone(user.password_hash)

    def test_check_password_correct(self):
        user = User(username='bob', email='bob@test.com')
        user.set_password('mypassword')
        self.assertTrue(user.check_password('mypassword'))
        self.assertFalse(user.check_password('wrongpassword'))

    def test_check_password_empty(self):
        user = User(username='charlie', email='charlie@test.com')
        user.set_password('mypassword')
        self.assertFalse(user.check_password(''))

    def test_check_username_uniqueness(self):
        self._create_user('user1', 'password1')
        with self.assertRaises(Exception):
            self._create_user('user1', 'password2')

    def test_check_email_uniqueness(self):
        self._create_user('user2', email='user2@test.com', password='password1')
        with self.assertRaises(Exception):
            self._create_user('user3', email='user2@test.com', password='password2')


# ---------------------------------------------------------------------------
# Score model: creation, correct field types, foreign key to User
# ---------------------------------------------------------------------------
class TestScoreModel(BaseTestCase):
    def test_score_creation_valid_fields(self):
        user_id = self._create_user()
        score_id = self._create_score(user_id, score=750, correct_answers=8, time_taken=42.5)
        saved = Score.query.get(score_id)
        self.assertEqual(saved.score, 750)
        self.assertEqual(saved.correct_answers, 8)
        self.assertEqual(saved.time_taken, 42.5)

    def test_score_fields_type_correctness(self):
        user_id = self._create_user()
        score_id = self._create_score(user_id, time_taken=30.7)
        self.assertIsInstance(Score.query.get(score_id).time_taken, float)
        self.assertIsInstance(Score.query.get(score_id).correct_answers, int)
        self.assertIsInstance(Score.query.get(score_id).score, int)
        self.assertIsInstance(Score.query.get(score_id).timestamp, datetime)

    def test_score_user_fk_relationship(self):
        user_id = self._create_user('fktestuser')
        score_id = self._create_score(user_id)
        self.assertEqual(Score.query.get(score_id).user.username, 'fktestuser')


# ---------------------------------------------------------------------------
# DailyScore model: uniqueness constraint (one score per user per day)
# ---------------------------------------------------------------------------
class TestDailyScoreModel(BaseTestCase):
    def test_daily_score_creation(self):
        user_id = self._create_user()
        daily_score_id = self._create_daily_score(user_id=user_id, reset_date=date.today(), score=600, correct_answers=7, time_taken=38.0)
        saved = DailyScore.query.get(daily_score_id)
        self.assertIsNotNone(saved)
        self.assertEqual(saved.score, 600)
        self.assertEqual(saved.correct_answers, 7)
        self.assertEqual(saved.time_taken, 38.0)
        self.assertEqual(saved.user_id, user_id)
 
    def test_uniqueness_constraint_prevents_duplicate_per_day(self):
        user_id = self._create_user()
        self._create_daily_score(user_id=user_id, reset_date=date.today())
        with self.assertRaises(Exception):
            self._create_daily_score(user_id=user_id, reset_date=date.today())
 
    def test_daily_score_user_fk_relationship(self):
        user_id = self._create_user('martinez')
        daily_score_id = self._create_daily_score(user_id=user_id)
        saved = DailyScore.query.get(daily_score_id)
        self.assertEqual(saved.user.username, 'martinez')



# ---------------------------------------------------------------------------
# ChallengeSession model: status transitions, foreign keys
# ---------------------------------------------------------------------------
class TestChallengeSessionModel(BaseTestCase):
    def _create_two_users(self):
        id1 = self._create_user('challenger', email='challenger@test.com')
        id2 = self._create_user('opponent', email='opponent@test.com')
        return id1, id2
 
    def _make_session(self, challenger_id, opponent_id, status='pending'):
        session = ChallengeSession(challenger_id=challenger_id, opponent_id=opponent_id, status=status)
        db.session.add(session)
        db.session.commit()
        return session.id
 
    def test_default_status_is_pending(self):
        id1, id2 = self._create_two_users()
        session_id = self._make_session(id1, id2)
        self.assertEqual(ChallengeSession.query.get(session_id).status, 'pending')
        
    def test_transition_pending_to_active_to_completed_and_winner(self):
        id1, id2 = self._create_two_users()
        session_id = self._make_session(id1, id2)
        session = ChallengeSession.query.get(session_id)
        session.status = 'active'
        db.session.commit()
        self.assertEqual(ChallengeSession.query.get(session_id).status, 'active')
        session.status = 'completed'
        db.session.commit()

        session = ChallengeSession.query.get(session_id)
        session.winner_id = id1
        db.session.commit()
        saved = ChallengeSession.query.get(session_id)
        self.assertEqual(saved.status, 'completed')
        self.assertEqual(saved.winner_id, id1)

    def test_transition_pending_to_declined(self):
        id1, id2 = self._create_two_users()
        session_id = self._make_session(id1, id2)
        session = ChallengeSession.query.get(session_id)
        session.status = 'declined'
        db.session.commit()
        self.assertEqual(ChallengeSession.query.get(session_id).status, 'declined')
 
    def test_challenger_opponent_user_fk_relationship(self):
        id1, id2 = self._create_two_users()
        session_id = self._make_session(id1, id2)
        self.assertEqual(ChallengeSession.query.get(session_id).challenger.username, 'challenger')
        self.assertEqual(ChallengeSession.query.get(session_id).opponent.username, 'opponent')

    def test_winner_fk_can_be_null(self):
        id1, id2 = self._create_two_users()
        session_id = self._make_session(id1, id2)
        self.assertIsNone(ChallengeSession.query.get(session_id).winner_id)

    def test_winner_user_fk_relationship(self):
        id1, id2 = self._create_two_users()
        session_id = self._make_session(id1, id2, status='active')
        session = ChallengeSession.query.get(session_id)
        session.status = 'completed'
        session.winner_id = id2
        db.session.commit()
        self.assertEqual(ChallengeSession.query.get(session_id).winner_id, id2)
 


if __name__ == '__main__':
    unittest.main()