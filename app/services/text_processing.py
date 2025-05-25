# Импорт необходимых модулей
from functools import lru_cache  # Для кэширования результатов функций
from pathlib import Path  # Для работы с путями файловой системы
from app.utils.embeddings import preprocess_text_to_embeddings, load_embeddings_from_file, process_text_with_limits
from app.utils.similarity import calculate_uniqueness_and_similarity
from app.utils.seo import calculate_spamminess, calculate_wateriness
from app.config import Config  # Конфигурация приложения
from app.utils.ai_text_detected import detect_ai_text
from app.utils.spell_checker import init_spell_checker, check_spelling_errors

spell_checker_tool = init_spell_checker()


@lru_cache(maxsize=32)  # Кэшируем результаты на 32 вызова для оптимизации
def _get_base_sentences_cache():
    """
    Загружает и кэширует эмбеддинги базовых документов из указанной папки.
    Возвращает словарь {имя_файла: эмбеддинги}

    Кэширование используется для:
    1. Ускорения последующих вызовов
    2. Снижения нагрузки на файловую систему
    3. Оптимизации использования памяти (maxsize=32)
    """
    base_sentences = {}
    base_folder_path = Path(Config.BASE_FOLDER)  # Получаем путь из конфига

    # Проверка существования папки
    if not base_folder_path.exists():
        raise FileNotFoundError("Base folder does not exist")

    # Рекурсивно обрабатываем все файлы в папке
    for base_file in base_folder_path.iterdir():
        if base_file.is_file():
            # Загружаем эмбеддинги для каждого файла
            base_sentences[base_file.name] = load_embeddings_from_file(base_file)
    return base_sentences


def process_text(text: str, language: str) -> dict:
    """
    Основная функция обработки текста, выполняющая:
    1. Анализ водянистости и спамности текста
    2. Преобразование текста в эмбеддинги
    3. Сравнение с базой документов
    4. Расчет уникальности с учетом объема заимствованного текста

    Args:
        text (str): Входной текст для анализа
        language (str): Язык текста (для обработки)

    Returns:
        dict: Результаты анализа с ключами:
            - overall_uniqueness: процент уникальности (учитывает объем текста)
            - file_similarity: процент заимствований из каждого файла (по объему)
            - water_score: показатель водянистости
            - spam_score: показатель спамности
            - matched_sentences: список заимствованных предложений
            - ai_text_detected: результат анализа на ИИ
            - spelling_errors: орфографические ошибки
    """
    # SEO-анализ текста
    water_score = calculate_wateriness(text)  # Расчет водянистости
    spam_score = calculate_spamminess(text)  # Расчет спамности

    # Анализ текста на написание ИИ
    ai_text_detected = detect_ai_text(text)

    # Получаем и эмбеддинги, и список предложений
    processed_data = process_text_with_limits(text)
    uploaded_embeddings = processed_data["embeddings"]
    sentences = processed_data["sentences"]

    # Проверка орфографии
    spelling_errors = check_spelling_errors(text, spell_checker_tool)

    # Получаем кэшированные эмбеддинги базы документов
    base_sentences = _get_base_sentences_cache()

    # Сравнение с базой документов (теперь с улучшенным алгоритмом)
    overall_uniqueness, file_similarity, matched_sentences, avg_file_similarity = calculate_uniqueness_and_similarity(
        uploaded_embeddings, base_sentences, sentences
    )

    # Добавляем дополнительную информацию для отладки и аналитики
    text_stats = {
        'total_sentences': len(sentences),
        'total_chars': len(text.strip()),
        'total_words': len(text.split()),
        'borrowed_sentences_count': len(matched_sentences)
    }

    # Формируем итоговый результат
    return {
        "overall_uniqueness": f"{overall_uniqueness:.2f}%",  # Новый расчет с учетом объема
        "file_similarity": file_similarity,  # Проценты заимствований по файлам (по объему)
        "water_score": water_score,  # Показатель водянистости
        "spam_score": spam_score,  # Показатель спамности
        "matched_sentences": matched_sentences,  # Заимствованные предложения для подсветки
        "ai_text_detected": ai_text_detected,  # Процент предложений написанных ИИ
        "spelling_errors": spelling_errors,  # Проверка орфографии
        "text_statistics": text_stats,  # Дополнительная статистика для анализа
        "avg_file_similarity": avg_file_similarity  # Средние проценты сходства (для совместимости)
    }