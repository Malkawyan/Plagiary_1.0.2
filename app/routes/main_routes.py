from flask import Blueprint, request, jsonify, send_from_directory
import logging
from langdetect import detect
from app.services.text_processing import process_text
from app.config import Config
from app.services.file_storage import get_unique_filename
from app.services.file_processing import read_file
import os
from datetime import datetime

main_routes = Blueprint('main', __name__)

@main_routes.route('/', methods=['GET'])
def serve_html():
    logging.info("Отправка главной страницы интерфейса пользователю.")
    return send_from_directory(Config.STATIC_FOLDER, 'index.html')

# @main_routes.route('/', methods=['POST'])
# def process_text_route():
#     text = request.form.get('text')
#     if not text:
#         logging.error("Ошибка: текст отсутствует в запросе.")
#         return jsonify({"error": "No text provided"}), 400
#
#     try:
#         language = detect(text)
#         result = process_text(text, language)
#         return jsonify(result)
#     except Exception as e:
#         logging.error(f"Произошла ошибка при обработке текста: {e}")
#         return jsonify({"error": "An error occurred"}), 500

# @main_routes.route('/', methods=['POST'])
# def process_text_route():
#     text = request.form.get('text')
#     if not text:
#         logging.error("Ошибка: текст отсутствует в запросе.")
#         return jsonify({"error": "No text provided"}), 400
#
#     try:
#         language = detect(text)
#         result = process_text(text, language)
#         return jsonify(result)
#     except Exception as e:
#         logging.error(f"Произошла ошибка при обработке текста: {e}")
#         return jsonify({"error": "An error occurred"}), 500


@main_routes.route('/', methods=['POST'])
def process_text_route():
    text = request.form.get('text')
    uploaded_file = request.files.get('file')  # Получаем загруженный файл

    if not text and not uploaded_file:
        logging.error("Ошибка: текст или файл отсутствуют в запросе.")
        return jsonify({"error": "No text or file provided"}), 400

    try:
        if uploaded_file:
            # Логируем имя файла
            logging.info(f"Получен файл: {uploaded_file.filename}")

            # Сохраняем загруженный файл с оригинальным именем (или уникальным, если имя занято)
            unique_filename = get_unique_filename(Config.UPLOAD_FOLDER, uploaded_file.filename)
            file_path = os.path.join(Config.UPLOAD_FOLDER, unique_filename)
            uploaded_file.save(file_path)
            logging.info(f"Файл сохранен: {file_path}")

            # Читаем текст из файла
            text = read_file(file_path)
        else:
            # Если файл не загружен, не сохраняем ничего в папку uploads
            logging.info("Файл не загружен, сохранение в папку uploads пропущено.")

        # Обрабатываем текст
        language = detect(text)
        result = process_text(text, language)
        return jsonify(result)
    except Exception as e:
        logging.error(f"Произошла ошибка при обработке текста: {e}")
        return jsonify({"error": "An error occurred"}), 500

