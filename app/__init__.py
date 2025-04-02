from flask import Flask
from app.routes.main_routes import main_routes
from app.config import Config

def create_app():
    app = Flask(__name__, static_folder='static', static_url_path='/static')
    app.config.from_object(Config)

    app.register_blueprint(main_routes)

    return app