from flask import Blueprint
from .main_routes import main_routes

# Создаем основной Blueprint для всех маршрутов
routes = Blueprint('routes', __name__)

# Регистрируем маршруты из модуля main_routes
routes.register_blueprint(main_routes)

# Экспортируем Blueprint для использования в основном приложении
__all__ = ['routes']