
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

def check_file_exists(folder, filename):
    """
    Проверяет, существует ли файл с указанным именем в папке.

    :param folder: Папка, в которой проверяется наличие файла.
    :param filename: Имя файла для проверки.
    :return: True, если файл существует, False - если нет.
    """
    file_path = os.path.join(folder, filename)
    return os.path.exists(file_path)