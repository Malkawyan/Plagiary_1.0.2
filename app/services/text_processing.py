import numpy as np
from app.utils.embeddings import preprocess_text_to_embeddings, load_embeddings_from_file
from app.utils.similarity import calculate_uniqueness_and_similarity
from app.utils.seo import calculate_spamminess, calculate_wateriness
from app.config import Config
from pathlib import Path

# Функция для обработки текста, вычисления его уникальности и заимствований
def process_text(text, language):
    """
        Обрабатывает текст, вычисляет его уникальность, заимствования, воду и спам.
        :param text: Входной текст для анализа.
        :param language: Язык текста (определяется перед вызовом).
        :return: Словарь с процентом уникальности, заимствованиями, уровнем воды и спама.
    """

    # Проверка воды в тексте
    water_score = calculate_wateriness(text)

    #Проверка спама в тексте
    spam_score = calculate_spamminess(text)

    # Преобразуем входной текст в эмбеддинги (векторные представления) с учётом языка
    uploaded_embeddings = preprocess_text_to_embeddings(text, language)

    # Создаём словарь для хранения эмбеддингов базовых файлов
    base_sentences = {}

    # Указываем путь к папке с базой данных файлов для проверки
    base_folder_path = Path(Config.BASE_FOLDER)

    # Проверяем, существует ли папка с базой данных
    if not base_folder_path.exists():
        raise FileNotFoundError("Base folder does not exist")  # Если папка не найдена, генерируем ошибку

    # Проходим по всем файлам в базе
    for base_file in base_folder_path.iterdir():
        # Проверяем, является ли объект файлом (не папкой)
        if base_file.is_file():
            # Загружаем эмбеддинги (векторные представления предложений) из каждого файла
            base_embeddings = load_embeddings_from_file(base_file)
            # Добавляем эмбеддинги в словарь, где ключом является имя файла
            base_sentences[base_file.name] = base_embeddings

    # Вычисляем общую уникальность и заимствования из всех файлов базы
    overall_uniqueness, file_similarity, matched_indices = calculate_uniqueness_and_similarity(uploaded_embeddings, base_sentences)

    # Возвращаем результат в виде словаря с процентом уникальности и заимствованиями
    return {
        "overall_uniqueness": f"{overall_uniqueness:.2f}%",  # Общая уникальность текста
        "file_similarity": file_similarity,  # Подобие с файлами из базы
        "water_score": water_score, # Процент воды в тексте
        "spam_score" : spam_score, # Процент спама в тексте
        "matched_indices" : matched_indices # Индексы неуникальных предложений
    }
