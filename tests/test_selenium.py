"""
Unittest + Selenium system tests for RateRace.

These tests require a live Flask server.

Terminal 1, from project root:
    py run.py

Terminal 2, from project root:
    py -m unittest tests.test_selenium

You can also run:
    py -m unittest discover -s tests

Optional environment variables:
    RATERACE_BASE_URL=http://127.0.0.1:5020
    SELENIUM_BROWSER=chrome
    HEADLESS=1
    SKIP_DB_SEED=1
"""

from __future__ import annotations

import json
import os

# server/config.py raises RuntimeError if these are missing.
# These values are only for the test process's direct app import/seeding.
# Your running Flask server still uses your real .env values.
os.environ.setdefault("SECRET_KEY", "selenium-test-secret-key")
os.environ.setdefault("TMDB_API_KEY", "selenium-test-tmdb-key")

import time
import unittest
import uuid
from datetime import datetime, timezone
from typing import Callable
from urllib.error import URLError
from urllib.request import urlopen

from selenium import webdriver
from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


BASE_URL = os.environ.get("RATERACE_BASE_URL", "http://127.0.0.1:5020").rstrip("/")
BROWSER = os.environ.get("SELENIUM_BROWSER", "chrome").lower()
HEADLESS = os.environ.get("HEADLESS", "0") == "1"


class RateRaceSeleniumTests(unittest.TestCase):
    """Live-server Selenium tests for RateRace."""

    @classmethod
    def setUpClass(cls):
        cls.wait_for_server(BASE_URL)

        from server import create_app, db

        cls.app = create_app()
        cls.db = db

        with cls.app.app_context():
            cls.db.create_all()

        if os.environ.get("SKIP_DB_SEED", "0") != "1":
            cls.seed_movies_for_game()

    def setUp(self):
        if BROWSER == "firefox":
            options = webdriver.FirefoxOptions()
            if HEADLESS:
                options.add_argument("--headless")
            self.driver = webdriver.Firefox(options=options)
        else:
            options = webdriver.ChromeOptions()
            options.add_argument("--window-size=1400,1000")
            if HEADLESS:
                options.add_argument("--headless=new")
            self.driver = webdriver.Chrome(options=options)

        self.driver.implicitly_wait(0)
        self.wait = WebDriverWait(self.driver, 15)

    def tearDown(self):
        self.driver.quit()

    @staticmethod
    def wait_for_server(base_url: str, timeout_seconds: int = 15) -> None:
        deadline = time.time() + timeout_seconds

        while time.time() < deadline:
            try:
                with urlopen(base_url, timeout=1) as response:
                    if response.status < 500:
                        return
            except URLError:
                time.sleep(0.25)

        raise AssertionError(f"Could not connect to {base_url}. Start Flask first with: py run.py")

    def page_text(self) -> str:
        return self.driver.find_element(By.TAG_NAME, "body").text

    def page_text_lower(self) -> str:
        return self.page_text().lower()

    def fail_with_page_state(self, action: str) -> None:
        self.fail(
            f"{action} timed out.\n\n"
            f"Current URL: {self.driver.current_url}\n\n"
            f"Visible page text:\n{self.page_text()[:3000]}"
        )

    @staticmethod
    def unique_account(prefix: str) -> dict[str, str]:
        suffix = uuid.uuid4().hex[:8]
        return {
            "username": f"{prefix}_{suffix}",
            "email": f"{prefix}_{suffix}@example.com",
            "password": "Password123!",
        }

    @staticmethod
    def safe_click(driver: WebDriver, element) -> None:
        try:
            element.click()
        except ElementClickInterceptedException:
            driver.execute_script("arguments[0].click();", element)

    def is_visible(self, element_id: str) -> bool:
        try:
            return self.driver.find_element(By.ID, element_id).is_displayed()
        except Exception:
            return False

    def wait_for_api_condition(
        self,
        endpoint: str,
        predicate: Callable[[dict], bool],
        timeout_seconds: int = 10,
    ) -> dict:
        deadline = time.time() + timeout_seconds
        last_data = {}

        while time.time() < deadline:
            try:
                with urlopen(f"{BASE_URL}{endpoint}", timeout=2) as response:
                    last_data = json.loads(response.read().decode("utf-8"))

                if predicate(last_data):
                    return last_data
            except Exception:
                pass

            time.sleep(0.25)

        self.fail(f"Timed out waiting for {endpoint}. Last response: {last_data}")

    @classmethod
    def seed_movies_for_game(cls):
        """Seed enough movies so /api/game/questions works without TMDB."""
        from server.models import Movie, SystemState

        test_movies = [
            ("The Selenium Redemption", "1994", 9.3),
            ("The Browserfather", "1972", 9.2),
            ("The Dark Test", "2008", 9.0),
            ("Schindler's Spec", "1993", 8.9),
            ("The Lord of the Clicks", "2003", 8.8),
            ("Pulp Fixture", "1994", 8.7),
            ("Forrest Gump Test", "1994", 8.6),
            ("Inception Test", "2010", 8.5),
            ("Fight Click", "1999", 8.4),
            ("The Matrix Test", "1999", 8.3),
            ("Good Tests", "1990", 8.2),
            ("Interstellar Selenium", "2014", 8.1),
            ("Seven Assertions", "1995", 8.0),
            ("The Silence of the Bugs", "1991", 7.9),
            ("Saving Private Pytest", "1998", 7.8),
            ("The Prestige Test", "2006", 7.7),
            ("The Departed Spec", "2006", 7.6),
            ("Parasite Test", "2019", 7.5),
            ("Gladiator Browser", "2000", 7.4),
            ("Whiplash WebDriver", "2014", 7.3),
            ("Django Unclicked", "2012", 7.2),
            ("The Lion Test", "1994", 7.1),
            ("Alien Assertion", "1979", 7.0),
            ("Back to the Browser", "1985", 6.9),
            ("Toy Story Test", "1995", 6.8),
            ("Finding Selenium", "2003", 6.7),
            ("The Green Mile Test", "1999", 6.6),
            ("Spirited Await", "2001", 6.5),
            ("City of Tests", "2002", 6.4),
            ("The Usual Selectors", "1995", 6.3),
        ]

        with cls.app.app_context():
            for i, (title, year, rating) in enumerate(test_movies):
                tmdb_id = 900000 + i

                if Movie.query.filter_by(tmdb_id=tmdb_id).first():
                    continue

                cls.db.session.add(Movie(
                    title=title,
                    year=year,
                    rating=rating,
                    tmdb_id=tmdb_id,
                    poster_url="/static/img/no-poster.png",
                ))

            now = datetime.now(timezone.utc).replace(tzinfo=None)
            state = SystemState.query.first()

            if state is None:
                state = SystemState(
                    last_refresh=now,
                    next_popular_page=1,
                    next_top_rated_page=1,
                )
                cls.db.session.add(state)
            else:
                state.last_refresh = now
                state.next_popular_page = state.next_popular_page or 1
                state.next_top_rated_page = state.next_top_rated_page or 1

            cls.db.session.commit()

    @classmethod
    def create_account_in_db(cls, account: dict[str, str]) -> None:
        from server.models import User

        with cls.app.app_context():
            existing = User.query.filter(
                (User.username == account["username"]) | (User.email == account["email"])
            ).first()

            if existing:
                return

            user = User(username=account["username"], email=account["email"])
            user.set_password(account["password"])
            cls.db.session.add(user)
            cls.db.session.commit()

    def register_account_through_ui(self, account: dict[str, str]) -> None:
        self.driver.get(f"{BASE_URL}/register")

        self.wait.until(EC.presence_of_element_located((By.NAME, "username"))).send_keys(account["username"])
        self.driver.find_element(By.NAME, "email").send_keys(account["email"])
        self.driver.find_element(By.NAME, "password").send_keys(account["password"])

        submit_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
        self.safe_click(self.driver, submit_button)

        try:
            self.wait.until(lambda d: d.current_url.rstrip("/") == BASE_URL)
        except TimeoutException:
            self.fail_with_page_state("Registration redirect to homepage")

        body = self.page_text_lower()
        self.assertTrue(
            account["username"].lower() in body or "sign out" in body,
            "Expected registered user to be logged in after registration",
        )

    def login_account(self, username: str, password: str, expect_success: bool) -> None:
        self.driver.get(f"{BASE_URL}/login")

        self.wait.until(EC.presence_of_element_located((By.NAME, "username"))).send_keys(username)
        self.driver.find_element(By.NAME, "password").send_keys(password)

        submit_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
        self.safe_click(self.driver, submit_button)

        if expect_success:
            try:
                self.wait.until(lambda d: d.current_url.rstrip("/") == BASE_URL)
                self.wait.until(
                    lambda d: username.lower() in self.page_text_lower() or "sign out" in self.page_text_lower()
                )
            except TimeoutException:
                self.fail_with_page_state("Login")
        else:
            try:
                self.wait.until(lambda d: "invalid username or password" in self.page_text_lower())
            except TimeoutException:
                self.fail_with_page_state("Wrong-password login")

    def speed_up_game_feedback(self) -> None:
        self.driver.execute_script(
            """
            if (!window.__seleniumOriginalSetTimeout) {
                window.__seleniumOriginalSetTimeout = window.setTimeout;
                window.setTimeout = function(callback, delay) {
                    return window.__seleniumOriginalSetTimeout(
                        callback,
                        Math.min(delay || 0, 50)
                    );
                };
            }
            """
        )

    def play_ten_round_game(self) -> int:
        self.driver.get(f"{BASE_URL}/game")

        try:
            self.wait.until(lambda d: "start game" in self.page_text_lower())
        except TimeoutException:
            self.fail_with_page_state("Loading game page")

        self.speed_up_game_feedback()

        start_button = self.wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[onclick*='startGame']"))
        )
        self.safe_click(self.driver, start_button)

        try:
            self.wait.until(EC.visibility_of_element_located((By.ID, "screen-game")))
            self.wait.until(lambda d: d.find_element(By.ID, "title-a").text.strip() != "")
            self.wait.until(lambda d: d.find_element(By.ID, "title-b").text.strip() != "")
        except TimeoutException:
            self.fail_with_page_state("Starting game")

        for round_number in range(1, 11):
            self.wait.until(lambda d: self.is_visible("screen-game"))

            card_a = self.wait.until(EC.presence_of_element_located((By.ID, "card-a")))
            self.safe_click(self.driver, card_a)

            if round_number < 10:
                try:
                    self.wait.until(
                        lambda d, expected=str(round_number + 1): (
                            self.is_visible("screen-game")
                            and d.find_element(By.ID, "round-display").text.strip() == expected
                            and d.find_element(By.ID, "title-a").text.strip() != ""
                            and d.find_element(By.ID, "title-b").text.strip() != ""
                        )
                    )
                except TimeoutException:
                    self.fail_with_page_state(f"Advancing from round {round_number}")
            else:
                try:
                    self.wait.until(EC.visibility_of_element_located((By.ID, "screen-results")))
                    self.wait.until(lambda d: d.find_element(By.ID, "result-score").text.strip() != "")
                except TimeoutException:
                    self.fail_with_page_state("Finishing game")

        score_text = self.driver.find_element(By.ID, "result-score").text.strip()
        self.assertTrue(score_text.isdigit(), f"Expected numeric final score, got {score_text!r}")
        return int(score_text)

    def test_01_homepage_loads(self):
        self.driver.get(BASE_URL)
        body = self.page_text_lower()

        self.assertIn("raterace", body)
        self.assertIn("play now", body)
        self.assertIn("leaderboard", body)

    def test_02_register_new_account_lands_on_homepage(self):
        account = self.unique_account("register")
        self.register_account_through_ui(account)

        body = self.page_text_lower()
        self.assertIn(account["username"].lower(), body)
        self.assertIn("sign out", body)

    def test_03_login_with_wrong_password_shows_error_message(self):
        account = self.unique_account("wrongpass")
        self.create_account_in_db(account)

        self.login_account(
            username=account["username"],
            password="WrongPassword123!",
            expect_success=False,
        )

        self.assertIn("invalid username or password", self.page_text_lower())

    def test_04_login_success_lands_on_homepage(self):
        account = self.unique_account("login")
        self.create_account_in_db(account)

        self.login_account(
            username=account["username"],
            password=account["password"],
            expect_success=True,
        )

        body = self.page_text_lower()
        self.assertIn(account["username"].lower(), body)
        self.assertIn("sign out", body)

    def test_05_protected_game_redirects_logged_out_user_to_login(self):
        self.driver.get(f"{BASE_URL}/game")

        try:
            self.wait.until(lambda d: "/login" in d.current_url or "log in" in self.page_text_lower())
        except TimeoutException:
            self.fail_with_page_state("Logged-out game redirect")

        self.assertTrue(
            "/login" in self.driver.current_url or "log in" in self.page_text_lower()
        )

    def test_06_login_play_game_scoreboard_and_profile_stats(self):
        account = self.unique_account("player")
        self.create_account_in_db(account)

        self.login_account(account["username"], account["password"], expect_success=True)

        final_score = self.play_ten_round_game()
        self.assertGreaterEqual(final_score, 0)
        self.assertLessEqual(final_score, 2000)

        self.wait_for_api_condition(
            "/api/scores/leaderboard",
            lambda data: any(
                row.get("username") == account["username"]
                for row in data.get("leaderboard", [])
            ),
            timeout_seconds=10,
        )

        self.driver.get(f"{BASE_URL}/scoreboard")

        try:
            self.wait.until(lambda d: "leaderboard" in self.page_text_lower())
            self.wait.until(
                lambda d: account["username"].lower()
                in d.find_element(By.ID, "leaderboard-body").text.lower()
            )
        except TimeoutException:
            self.fail_with_page_state("Loading scoreboard")

        scoreboard_text = self.driver.find_element(By.ID, "leaderboard-body").text.lower()
        self.assertIn(account["username"].lower(), scoreboard_text)

        profile_link = self.wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href='/profile']"))
        )
        self.safe_click(self.driver, profile_link)

        try:
            self.wait.until(EC.url_contains("/profile"))
            self.wait.until(lambda d: "player profile" in self.page_text_lower())
        except TimeoutException:
            self.fail_with_page_state("Loading profile")

        profile_text = self.page_text_lower()
        self.assertIn(account["username"].lower(), profile_text)
        self.assertIn("leaderboard rank", profile_text)
        self.assertIn("best score", profile_text)
        self.assertIn("best accuracy", profile_text)
        self.assertIn("games played", profile_text)
        self.assertIn("average points", profile_text)
        self.assertIn("average accuracy", profile_text)
        self.assertIn("average time taken", profile_text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
