import os
from app.config import Config

def save_uploaded_file(uploaded_file):
    """
    Сохраняет загруженный файл в папку uploads с оригинальным именем.

    :param uploaded_file: Файл, загруженный пользователем.
    :return: Путь к сохраненному файлу.
    """
    if not uploaded_file:
        return None

    original_filename = uploaded_file.filename
    file_path = os.path.join(Config.UPLOAD_FOLDER, original_filename)
    uploaded_file.save(file_path)
    return file_path

def get_unique_filename(folder, filename):
    """
    Генерирует уникальное имя файла, добавляя суффикс, если файл с таким именем уже существует.

    :param folder: Папка, в которой будет сохранен файл.
    :param filename: Исходное имя файла.
    :return: Уникальное имя файла.
    """
    base_name, extension = os.path.splitext(filename)  # Разделяем имя и расширение
    counter = 1
    unique_name = filename

    # Проверяем, существует ли файл с таким именем
    while os.path.exists(os.path.join(folder, unique_name)):
        unique_name = f"{base_name}_{counter}{extension}"  # Добавляем суффикс
        counter += 1

    return unique_name