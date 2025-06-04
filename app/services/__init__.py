from .text_processing import process_text
from .file_processing import read_file
from .file_storage import check_file_exists

# Экспортируем функции для удобного импорта
__all__ = [
    "process_text",  # Функция для обработки текста
    "read_file",     # Функция для чтения файлов
    "check_file_exists",
]