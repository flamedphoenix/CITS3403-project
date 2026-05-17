import os
from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_socketio import SocketIO
db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = 'main.login'
socketio = SocketIO()

def create_app(config_class=None):
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'client', 'templates'),
        static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'client', 'static'),
    )
    if config_class is None:
        from server.config import Config
        config_class = Config
    app.config.from_object(config_class)
    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    socketio.init_app(app)

    from server.routes import main
    app.register_blueprint(main)

    from server import models
    from server import challenge

    return app


