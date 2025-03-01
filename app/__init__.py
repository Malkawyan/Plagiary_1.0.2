from flask import Flask
from app.routes.main_routes import main_routes
from app.config import Config

def create_app():
    app = Flask(__name__, static_folder='app/static')
    app.config.from_object(Config)

    app.register_blueprint(main_routes)

    return app