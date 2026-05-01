from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_user, current_user, logout_user
from server.forms import LoginForm, RegistrationForm
from server.models import User
from server import db


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
            flash('Account already exists with that username and email')
            return redirect(url_for('main.register'))
        
        if existing_user:
            flash('Username already taken')
            return redirect(url_for('main.register'))

        if existing_email:
            flash('Email already registered')
            return redirect(url_for('main.register'))
        
        user=User(username=form.username.data, email=form.email.data)
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
