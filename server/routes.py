from flask import Blueprint, render_template, redirect, url_for

main = Blueprint('main', __name__)


@main.route('/')
def index():
    return render_template('index.html')


@main.route('/game')
def game():
    return render_template('game.html')


@main.route('/scoreboard')
def scoreboard():
    return render_template('scoreboard.html')


@main.route('/login')
def login():
    return render_template('login.html')


@main.route('/register')
def register():
    return render_template('register.html')


@main.route('/logout')
def logout():
    return redirect(url_for('main.index'))
