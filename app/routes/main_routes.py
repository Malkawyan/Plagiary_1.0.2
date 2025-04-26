from flask import Blueprint, request, jsonify, send_from_directory
import logging
from langdetect import detect
from app.services.text_processing import process_text
from app.config import Config
from app.services.file_storage import get_unique_filename
from app.services.file_processing import read_file
import os

main_routes = Blueprint('main', __name__)

@main_routes.route('/', methods=['GET'])
def serve_html():
    """
        Отправляет главную страницу интерфейса пользователю.
        :return: HTML-файл главной страницы.
    """
    logging.info("Отправка главной страницы интерфейса пользователю.")
    return send_from_directory(Config.STATIC_FOLDER, 'index.html')

@main_routes.route('/<path:filename>')
def serve_static(filename):
    """
    Обслуживает статические файлы из папки static
    """
    return send_from_directory(Config.STATIC_FOLDER, filename)

@main_routes.route('/', methods=['POST'])
def process_text_route():
    """
       Обрабатывает текст, переданный в запросе, либо извлекает его из загруженного файла.
       :return: JSON с результатом обработки текста или сообщением об ошибке.
    """
    text = request.form.get('text')
    uploaded_file = request.files.get('file')  # Получаем загруженный файл

    if not text and not uploaded_file:
        logging.error("Ошибка: текст или файл отсутствуют в запросе.")
        return jsonify({"error": "No text or file provided"}), 400

    try:
        # Всегда используем текст из формы, если он есть
        if text:
            logging.info("Используется текст из поля ввода")
            language = detect(text)
            result = process_text(text, language)
            return jsonify(result)

        # Только если текста нет — читаем файл
        if uploaded_file:
            unique_filename = get_unique_filename(Config.UPLOAD_FOLDER, uploaded_file.filename)
            file_path = os.path.join(Config.UPLOAD_FOLDER, unique_filename)
            uploaded_file.save(file_path)
            text = read_file(file_path)
            language = detect(text)
            result = process_text(text, language)
            return jsonify(result)

    except Exception as e:
        logging.error(f"Произошла ошибка при обработке текста: {e}")
        return jsonify({"error": "An error occurred"}), 500