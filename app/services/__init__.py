from .text_processing import process_text
from .file_processing import read_file
from .file_storage import get_unique_filename

# Экспортируем функции для удобного импорта
__all__ = [
    "process_text",  # Функция для обработки текста
    "read_file",     # Функция для чтения файлов
    "get_unique_filename",
]