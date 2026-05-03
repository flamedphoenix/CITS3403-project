import os
from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from server.config import Config

db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = 'main.login'

def create_app():
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'client', 'templates'),
        static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'client', 'static'),
    )
    app.config.from_object(Config)
    db.init_app(app)
    migrate.init_app(app, db)


    login.init_app(app) 


    from server.routes import main
    app.register_blueprint(main)

    from server import models 

    return app


