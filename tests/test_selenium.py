"""
Selenium system tests for RateRace.

Start Flask in another terminal first:

    py run.py

Then run from project root:

    py -m pytest tests/test_selenium.py
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
from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


BASE_URL = os.environ.get("RATERACE_BASE_URL", "http://127.0.0.1:5020").rstrip("/")
BROWSER = os.environ.get("SELENIUM_BROWSER", "chrome").lower()
HEADLESS = os.environ.get("HEADLESS", "0") == "1"


def wait_for_server(base_url: str, timeout_seconds: int = 15) -> None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            with urlopen(base_url, timeout=1) as response:
                if response.status < 500:
                    return
        except URLError:
            time.sleep(0.25)
    pytest.fail(f"Could not connect to {base_url}. Start Flask first with: py run.py")


def page_text(driver: WebDriver) -> str:
    return driver.find_element(By.TAG_NAME, "body").text


def fail_with_page_state(driver: WebDriver, action: str) -> None:
    pytest.fail(
        f"{action} timed out.\n\n"
        f"Current URL: {driver.current_url}\n\n"
        f"Visible page text:\n{page_text(driver)[:3000]}"
    )


def unique_account(prefix: str) -> dict[str, str]:
    suffix = uuid.uuid4().hex[:8]
    return {
        "username": f"{prefix}_{suffix}",
        "email": f"{prefix}_{suffix}@example.com",
        "password": "Password123!",
    }


def safe_click(driver: WebDriver, element) -> None:
    try:
        element.click()
    except ElementClickInterceptedException:
        driver.execute_script("arguments[0].click();", element)


def is_visible(driver: WebDriver, element_id: str) -> bool:
    try:
        return driver.find_element(By.ID, element_id).is_displayed()
    except Exception:
        return False


def wait_for_api_condition(endpoint: str, predicate: Callable[[dict], bool], timeout_seconds: int = 10) -> dict:
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
    pytest.fail(f"Timed out waiting for {endpoint}. Last response: {last_data}")


@pytest.fixture(scope="session")
def app_and_db():
    from server import create_app, db
    app = create_app()
    with app.app_context():
        db.create_all()
    return app, db


@pytest.fixture(scope="session", autouse=True)
def seed_movies_for_game(app_and_db):
    if os.environ.get("SKIP_DB_SEED", "0") == "1":
        return

    app, db = app_and_db
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

    with app.app_context():
        for i, (title, year, rating) in enumerate(test_movies):
            tmdb_id = 900000 + i
            if Movie.query.filter_by(tmdb_id=tmdb_id).first():
                continue
            db.session.add(Movie(
                title=title,
                year=year,
                rating=rating,
                tmdb_id=tmdb_id,
                poster_url="/static/img/no-poster.png",
            ))

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        state = SystemState.query.first()
        if state is None:
            state = SystemState(last_refresh=now, next_popular_page=1, next_top_rated_page=1)
            db.session.add(state)
        else:
            state.last_refresh = now
            state.next_popular_page = state.next_popular_page or 1
            state.next_top_rated_page = state.next_top_rated_page or 1

        db.session.commit()


def create_account_in_db(app_and_db, account: dict[str, str]) -> None:
    app, db = app_and_db
    from server.models import User

    with app.app_context():
        existing = User.query.filter(
            (User.username == account["username"]) | (User.email == account["email"])
        ).first()
        if existing:
            return

        user = User(username=account["username"], email=account["email"])
        user.set_password(account["password"])
        db.session.add(user)
        db.session.commit()


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
        options.add_argument("--window-size=1400,1000")
        if HEADLESS:
            options.add_argument("--headless=new")
        browser = webdriver.Chrome(options=options)

    browser.implicitly_wait(0)
    yield browser
    browser.quit()


@pytest.fixture
def wait(driver):
    return WebDriverWait(driver, 15)


def register_account_through_ui(driver: WebDriver, wait: WebDriverWait, account: dict[str, str]) -> None:
    driver.get(f"{BASE_URL}/register")

    wait.until(EC.presence_of_element_located((By.NAME, "username"))).send_keys(account["username"])
    driver.find_element(By.NAME, "email").send_keys(account["email"])
    driver.find_element(By.NAME, "password").send_keys(account["password"])

    submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
    safe_click(driver, submit_button)

    try:
        wait.until(lambda d: d.current_url.rstrip("/") == BASE_URL)
    except TimeoutException:
        fail_with_page_state(driver, "Registration redirect to homepage")

    body = page_text(driver).lower()
    if account["username"].lower() not in body and "sign out" not in body:
        fail_with_page_state(driver, "Registration login/navbar check")


def login_account(driver: WebDriver, wait: WebDriverWait, username: str, password: str, expect_success: bool) -> None:
    driver.get(f"{BASE_URL}/login")

    wait.until(EC.presence_of_element_located((By.NAME, "username"))).send_keys(username)
    driver.find_element(By.NAME, "password").send_keys(password)

    submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
    safe_click(driver, submit_button)

    if expect_success:
        try:
            wait.until(lambda d: d.current_url.rstrip("/") == BASE_URL)
            wait.until(lambda d: username.lower() in page_text(d).lower() or "sign out" in page_text(d).lower())
        except TimeoutException:
            fail_with_page_state(driver, "Login")
    else:
        try:
            wait.until(EC.text_to_be_present_in_element((By.TAG_NAME, "body"), "Invalid username or password"))
        except TimeoutException:
            fail_with_page_state(driver, "Wrong-password login")


def speed_up_game_feedback(driver: WebDriver) -> None:
    driver.execute_script(
        """
        if (!window.__seleniumOriginalSetTimeout) {
            window.__seleniumOriginalSetTimeout = window.setTimeout;
            window.setTimeout = function(callback, delay) {
                return window.__seleniumOriginalSetTimeout(callback, Math.min(delay || 0, 50));
            };
        }
        """
    )


def play_ten_round_game(driver: WebDriver, wait: WebDriverWait) -> int:
    driver.get(f"{BASE_URL}/game")

    try:
        wait.until(lambda d: "start game" in page_text(d).lower())
    except TimeoutException:
        fail_with_page_state(driver, "Loading game page")

    speed_up_game_feedback(driver)

    start_button = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "button[onclick*='startGame']"))
    )
    safe_click(driver, start_button)

    try:
        wait.until(EC.visibility_of_element_located((By.ID, "screen-game")))
        wait.until(lambda d: d.find_element(By.ID, "title-a").text.strip() != "")
        wait.until(lambda d: d.find_element(By.ID, "title-b").text.strip() != "")
    except TimeoutException:
        fail_with_page_state(driver, "Starting game")

    for round_number in range(1, 11):
        wait.until(lambda d: is_visible(d, "screen-game"))

        card_a = wait.until(EC.presence_of_element_located((By.ID, "card-a")))
        safe_click(driver, card_a)

        if round_number < 10:
            try:
                wait.until(
                    lambda d, expected=str(round_number + 1): (
                        is_visible(d, "screen-game")
                        and d.find_element(By.ID, "round-display").text.strip() == expected
                        and d.find_element(By.ID, "title-a").text.strip() != ""
                        and d.find_element(By.ID, "title-b").text.strip() != ""
                    )
                )
            except TimeoutException:
                fail_with_page_state(driver, f"Advancing from round {round_number}")
        else:
            try:
                wait.until(EC.visibility_of_element_located((By.ID, "screen-results")))
                wait.until(lambda d: d.find_element(By.ID, "result-score").text.strip() != "")
            except TimeoutException:
                fail_with_page_state(driver, "Finishing game")

    score_text = driver.find_element(By.ID, "result-score").text.strip()
    assert score_text.isdigit()
    return int(score_text)


def test_register_new_account_lands_on_homepage(driver, wait):
    account = unique_account("register")
    register_account_through_ui(driver, wait, account)


def test_login_with_wrong_password_shows_error_message(driver, wait, app_and_db):
    account = unique_account("wrongpass")
    create_account_in_db(app_and_db, account)

    login_account(
        driver,
        wait,
        username=account["username"],
        password="WrongPassword123!",
        expect_success=False,
    )


def test_login_play_game_scoreboard_and_profile_stats(driver, wait, app_and_db):
    account = unique_account("player")
    create_account_in_db(app_and_db, account)

    login_account(driver, wait, account["username"], account["password"], expect_success=True)

    final_score = play_ten_round_game(driver, wait)
    assert 0 <= final_score <= 2000

    wait_for_api_condition(
        "/api/scores/leaderboard",
        lambda data: any(row.get("username") == account["username"] for row in data.get("leaderboard", [])),
        timeout_seconds=10,
    )

    driver.get(f"{BASE_URL}/scoreboard")
    try:
        wait.until(lambda d: "leaderboard" in page_text(d).lower())
        wait.until(lambda d: account["username"].lower() in d.find_element(By.ID, "leaderboard-body").text.lower())
    except TimeoutException:
        fail_with_page_state(driver, "Loading scoreboard")

    scoreboard_text = driver.find_element(By.ID, "leaderboard-body").text
    assert account["username"].lower() in scoreboard_text.lower()

    try:
        profile_link = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href='/profile']")))
    except TimeoutException:
        fail_with_page_state(driver, "Finding profile link")

    safe_click(driver, profile_link)

    try:
        wait.until(EC.url_contains("/profile"))
        wait.until(lambda d: "player profile" in page_text(d).lower())
    except TimeoutException:
        fail_with_page_state(driver, "Loading profile")

    profile_text = page_text(driver)
    profile_text_lower = profile_text.lower()

    assert account["username"].lower() in profile_text_lower
    assert "leaderboard rank" in profile_text_lower
    assert "best score" in profile_text_lower
    assert "best accuracy" in profile_text_lower
    assert "games played" in profile_text_lower
    assert "average points" in profile_text_lower
    assert "average accuracy" in profile_text_lower
    assert "average time taken" in profile_text_lower