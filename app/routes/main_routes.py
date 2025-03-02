from flask import Blueprint, request, jsonify, send_from_directory
import logging
from langdetect import detect
from app.services.text_processing import process_text
from app.config import Config

main_routes = Blueprint('main', __name__)

@main_routes.route('/', methods=['GET'])
def serve_html():
    logging.info("Отправка главной страницы интерфейса пользователю.")
    return send_from_directory(Config.STATIC_FOLDER, 'index.html')

@main_routes.route('/', methods=['POST'])
def process_text_route():
    text = request.form.get('text')
    if not text:
        logging.error("Ошибка: текст отсутствует в запросе.")
        return jsonify({"error": "No text provided"}), 400

    try:
        language = detect(text)
        result = process_text(text, language)
        return jsonify(result)
    except Exception as e:
        logging.error(f"Произошла ошибка при обработке текста: {e}")
        return jsonify({"error": "An error occurred"}), 500

