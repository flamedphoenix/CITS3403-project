"""
Selenium system tests for RateRace.

What this covers:
- Register a new account -> lands on homepage
- Login with wrong password -> sees error message
- Login -> play a 10-round game -> score appears on leaderboard
- View profile page -> stats show up after playing
- View scoreboard -> user appears in table

Before running these tests, start the Flask app in another terminal:

    py run.py

Then run from the project root:

    py -m pytest tests/test_selenium.py

Useful optional environment variables:

    RATERACE_BASE_URL=http://127.0.0.1:5020
    SELENIUM_BROWSER=chrome
    HEADLESS=1
    SKIP_DB_SEED=1

Notes:
- These tests use the real browser and your real Flask routes.
- The test seeds local movie rows directly into your SQLite database so the game can
  run without relying on TMDB during Selenium testing.
"""

from __future__ import annotations

import json
import os

os.environ.setdefault("SECRET_KEY", "selenium-test-secret-key")
os.environ.setdefault("TMDB_API_KEY", "selenium-test-tmdb-key")

import time
import uuid
from datetime import datetime, timezone
from typing import Callable
from urllib.error import URLError
from urllib.request import urlopen

import pytest
from selenium import webdriver
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


BASE_URL = os.environ.get("RATERACE_BASE_URL", "http://127.0.0.1:5020").rstrip("/")
BROWSER = os.environ.get("SELENIUM_BROWSER", "chrome").lower()
HEADLESS = os.environ.get("HEADLESS", "0") == "1"


# ---------------------------------------------------------------------------
# General helpers
# ---------------------------------------------------------------------------

def wait_for_server(base_url: str, timeout_seconds: int = 15) -> None:
    """Fail clearly if the Flask app is not running."""
    deadline = time.time() + timeout_seconds

    while time.time() < deadline:
        try:
            with urlopen(base_url, timeout=1) as response:
                if response.status < 500:
                    return
        except URLError:
            time.sleep(0.25)

    pytest.fail(
        f"Could not connect to {base_url}. "
        "Start the Flask app first with: py run.py"
    )


def page_text(driver: WebDriver) -> str:
    return driver.find_element(By.TAG_NAME, "body").text


def unique_account(prefix: str = "selenium") -> dict[str, str]:
    suffix = uuid.uuid4().hex[:8]
    return {
        "username": f"{prefix}_{suffix}",
        "email": f"{prefix}_{suffix}@example.com",
        "password": "Password123!",
    }


def safe_click(driver: WebDriver, element) -> None:
    """Click normally, falling back to JS click if something intercepts it."""
    try:
        element.click()
    except ElementClickInterceptedException:
        driver.execute_script("arguments[0].click();", element)


def is_visible(driver: WebDriver, element_id: str) -> bool:
    try:
        return driver.find_element(By.ID, element_id).is_displayed()
    except Exception:
        return False


def wait_for_api_condition(
    endpoint: str,
    predicate: Callable[[dict], bool],
    timeout_seconds: int = 10,
) -> dict:
    """Poll a JSON API endpoint until predicate(data) is true."""
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

    pytest.fail(f"Timed out waiting for API condition on {endpoint}. Last data: {last_data}")


# ---------------------------------------------------------------------------
# Database seed helper
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session", autouse=True)
def seed_movies_for_game():
    """
    Seed enough movies for /api/game/questions to return 10 playable rounds.

    This prevents the Selenium tests from depending on TMDB/network data.
    Set SKIP_DB_SEED=1 if you want to use your existing seeded database instead.
    """
    if os.environ.get("SKIP_DB_SEED", "0") == "1":
        return

    try:
        from server import create_app, db
        from server.models import Movie, SystemState
    except Exception as exc:
        pytest.fail(
            "Could not import the Flask app for test seeding. "
            "Run pytest from the project root. "
            f"Original error: {exc}"
        )

    app = create_app()

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

    with app.app_context():
        for i, (title, year, rating) in enumerate(test_movies):
            tmdb_id = 900000 + i
            if Movie.query.filter_by(tmdb_id=tmdb_id).first():
                continue

            movie_kwargs = {
                "title": title,
                "year": year,
                "rating": rating,
                "tmdb_id": tmdb_id,
            }

            # Your current Movie model has this field. This hasattr check keeps
            # the test safer if an older schema is used.
            if hasattr(Movie, "poster_url"):
                movie_kwargs["poster_url"] = "/static/img/no-poster.png"

            db.session.add(Movie(**movie_kwargs))

        # Keep maintain_movie_cache() from trying to refresh from TMDB during tests.
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        state = SystemState.query.first()

        if state is None:
            state = SystemState(last_refresh=now)

            if hasattr(SystemState, "next_popular_page"):
                state.next_popular_page = 1

            if hasattr(SystemState, "next_top_rated_page"):
                state.next_top_rated_page = 1

            db.session.add(state)
        else:
            state.last_refresh = now

        db.session.commit()


# ---------------------------------------------------------------------------
# Selenium fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def driver():
    wait_for_server(BASE_URL)

    if BROWSER == "firefox":
        options = webdriver.FirefoxOptions()
        if HEADLESS:
            options.add_argument("--headless")
        browser = webdriver.Firefox(options=options)
    else:
        options = webdriver.ChromeOptions()
        if HEADLESS:
            options.add_argument("--headless=new")
        options.add_argument("--window-size=1400,1000")
        browser = webdriver.Chrome(options=options)

    browser.implicitly_wait(0)
    yield browser
    browser.quit()


@pytest.fixture
def wait(driver):
    return WebDriverWait(driver, 15)


# ---------------------------------------------------------------------------
# UI flow helpers
# ---------------------------------------------------------------------------

def register_account(driver: WebDriver, wait: WebDriverWait, account: dict[str, str]) -> None:
    driver.get(f"{BASE_URL}/register")

    wait.until(EC.presence_of_element_located((By.NAME, "username"))).send_keys(account["username"])
    driver.find_element(By.NAME, "email").send_keys(account["email"])
    driver.find_element(By.NAME, "password").send_keys(account["password"])

    submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    safe_click(driver, submit_button)

    wait.until(EC.url_to(f"{BASE_URL}/"))
    wait.until(EC.presence_of_element_located((By.LINK_TEXT, "Sign Out")))

    body = page_text(driver)
    assert account["username"] in body
    assert "Sign Out" in body


def logout(driver: WebDriver, wait: WebDriverWait) -> None:
    driver.get(f"{BASE_URL}/logout")
    wait.until(EC.presence_of_element_located((By.LINK_TEXT, "Log In")))


def login_account(
    driver: WebDriver,
    wait: WebDriverWait,
    username: str,
    password: str,
    expect_success: bool,
) -> None:
    driver.get(f"{BASE_URL}/login")

    wait.until(EC.presence_of_element_located((By.NAME, "username"))).send_keys(username)
    driver.find_element(By.NAME, "password").send_keys(password)

    submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    safe_click(driver, submit_button)

    if expect_success:
        wait.until(EC.url_to(f"{BASE_URL}/"))
        wait.until(EC.presence_of_element_located((By.LINK_TEXT, "Sign Out")))
        assert username in page_text(driver)
    else:
        wait.until(
            EC.text_to_be_present_in_element(
                (By.TAG_NAME, "body"),
                "Invalid username or password",
            )
        )


def speed_up_game_feedback(driver: WebDriver) -> None:
    """
    Your game waits 2 seconds between rounds for feedback.
    That is good for humans but slow for tests, so this shortens only the
    browser-side setTimeout delay.
    """
    driver.execute_script(
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


def choose_correct_card(driver: WebDriver) -> str:
    """
    Use the page's current game state to pick the higher-rated movie.
    This still clicks through the real UI, but avoids random low scores.
    """
    return driver.execute_script(
        """
        const pair = state.pairs[state.round];
        return pair[0].rating >= pair[1].rating ? 'a' : 'b';
        """
    )


def play_ten_round_game(driver: WebDriver, wait: WebDriverWait) -> int:
    driver.get(f"{BASE_URL}/game")

    wait.until(EC.text_to_be_present_in_element((By.TAG_NAME, "body"), "Start Game"))
    speed_up_game_feedback(driver)

    start_button = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(normalize-space(.), 'Start Game')]")
        )
    )
    safe_click(driver, start_button)

    wait.until(EC.visibility_of_element_located((By.ID, "screen-game")))
    wait.until(lambda d: d.find_element(By.ID, "title-a").text.strip() != "")
    wait.until(lambda d: d.find_element(By.ID, "title-b").text.strip() != "")

    for round_number in range(1, 11):
        wait.until(lambda d: is_visible(d, "screen-game"))

        choice = choose_correct_card(driver)
        card = wait.until(EC.presence_of_element_located((By.ID, f"card-{choice}")))
        safe_click(driver, card)

        if round_number < 10:
            wait.until(
                lambda d, expected=str(round_number + 1): (
                    is_visible(d, "screen-game")
                    and d.find_element(By.ID, "round-display").text.strip() == expected
                    and d.find_element(By.ID, "title-a").text.strip() != ""
                    and d.find_element(By.ID, "title-b").text.strip() != ""
                )
            )
        else:
            wait.until(EC.visibility_of_element_located((By.ID, "screen-results")))
            wait.until(lambda d: d.find_element(By.ID, "result-score").text.strip() != "")

    score_text = driver.find_element(By.ID, "result-score").text.strip()
    assert score_text.isdigit()
    return int(score_text)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_register_new_account_lands_on_homepage(driver, wait):
    account = unique_account("register")
    register_account(driver, wait, account)


def test_login_with_wrong_password_shows_error_message(driver, wait):
    account = unique_account("wrongpass")

    register_account(driver, wait, account)
    logout(driver, wait)

    login_account(
        driver,
        wait,
        username=account["username"],
        password="WrongPassword123!",
        expect_success=False,
    )


def test_login_play_game_scoreboard_and_profile_stats(driver, wait):
    account = unique_account("player")

    # Register first so the account exists, then log out and test the login flow.
    register_account(driver, wait, account)
    logout(driver, wait)
    login_account(driver, wait, account["username"], account["password"], expect_success=True)

    final_score = play_ten_round_game(driver, wait)
    assert 0 <= final_score <= 2000

    # Wait until the backend leaderboard API has saved this user's score.
    wait_for_api_condition(
        "/api/scores/leaderboard",
        lambda data: any(
            row.get("username") == account["username"]
            for row in data.get("leaderboard", [])
        ),
        timeout_seconds=10,
    )

    # View scoreboard: user appears in table.
    driver.get(f"{BASE_URL}/scoreboard")
    wait.until(EC.text_to_be_present_in_element((By.TAG_NAME, "body"), "Leaderboard"))
    wait.until(
        lambda d: account["username"].lower()
        in d.find_element(By.ID, "leaderboard-body").text.lower()
    )

    scoreboard_text = driver.find_element(By.ID, "leaderboard-body").text
    assert account["username"] in scoreboard_text

    # View profile page by clicking the username in the top bar.
    profile_link = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, account["username"])))
    safe_click(driver, profile_link)

    wait.until(EC.url_contains("/profile"))
    wait.until(EC.text_to_be_present_in_element((By.TAG_NAME, "body"), "Player Profile"))

    profile_text = page_text(driver)
    assert account["username"] in profile_text
    assert "Leaderboard Rank" in profile_text
    assert "Best Score" in profile_text
    assert "Best Accuracy" in profile_text
    assert "Games Played" in profile_text
    assert "Average Points" in profile_text
    assert "Average Accuracy" in profile_text
    assert "Average Time Taken" in profile_text
