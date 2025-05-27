from sentence_transformers import util
import re
import numpy as np
from .model_loader import model_loader

# Эталонные примеры для сравнения
spam_examples = [
    "Купи сейчас! Супер скидки! Бесплатно! Волшебный метод! Успей!",
    "СРОЧНО! Не упустите шанс! Только сегодня! Уникальное предложение! Кликните сейчас!",
    "100% результат гарантирован! Лучший продукт на рынке! Быстрые результаты!",
    "Заработай миллион за неделю! Секретная методика! Ограниченное предложение!"
]

normal_examples = [
    "Это обычный информативный текст без лишних слов и повторов.",
    "В статье рассматриваются основные принципы работы алгоритма и его применение.",
    "Исследование показало, что данный метод является эффективным для решения задачи.",
    "Анализ результатов демонстрирует значительное улучшение производительности системы."
]

watery_examples = [
    "Можно сказать, что в некотором роде, возможно, этот текст содержит, так сказать, довольно много слов, которые, по сути, не несут особой смысловой нагрузки.",
    "Как известно, многие эксперты считают, что возможно, вероятно, этот подход имеет определенные особенности, которые, в некотором смысле, могли бы потенциально иметь значение.",
    "Следует отметить, что, как правило, в большинстве случаев, зачастую можно наблюдать тенденцию к тому, что подобные тексты характеризуются наличием избыточной информации."
]

# Кэшируем эмбеддинги эталонных примеров
spam_embeddings = None
normal_embeddings = None
watery_embeddings = None


def _get_sentence_transformer_model():
    """Получает модель SentenceTransformer с проверкой загрузки"""
    model = model_loader.model
    if model is None:
        model_loader.logger.error("SentenceTransformer модель не загружена")
        raise RuntimeError("SentenceTransformer модель недоступна")
    return model


def _get_spam_embeddings():
    """Получает эмбеддинги спам-примеров с кэшированием"""
    global spam_embeddings
    if spam_embeddings is None:
        try:
            model = _get_sentence_transformer_model()
            spam_embeddings = model.encode(spam_examples, convert_to_tensor=True)
            model_loader.logger.info("Спам-эмбеддинги закэшированы")
        except Exception as e:
            model_loader.logger.error(f"Ошибка при создании спам-эмбеддингов: {e}")
            raise
    return spam_embeddings


def _get_normal_embeddings():
    """Получает эмбеддинги нормальных примеров с кэшированием"""
    global normal_embeddings
    if normal_embeddings is None:
        try:
            model = _get_sentence_transformer_model()
            normal_embeddings = model.encode(normal_examples, convert_to_tensor=True)
            model_loader.logger.info("Нормальные эмбеддинги закэшированы")
        except Exception as e:
            model_loader.logger.error(f"Ошибка при создании нормальных эмбеддингов: {e}")
            raise
    return normal_embeddings


def _get_watery_embeddings():
    """Получает эмбеддинги водянистых примеров с кэшированием"""
    global watery_embeddings
    if watery_embeddings is None:
        try:
            model = _get_sentence_transformer_model()
            watery_embeddings = model.encode(watery_examples, convert_to_tensor=True)
            model_loader.logger.info("Водянистые эмбеддинги закэшированы")
        except Exception as e:
            model_loader.logger.error(f"Ошибка при создании водянистых эмбеддингов: {e}")
            raise
    return watery_embeddings


def _count_spam_markers(text):
    """
    Подсчитывает количество спам-маркеров в тексте.

    Маркеры: восклицательные знаки, ALL CAPS слова, слова-триггеры спама
    """
    spam_words = ['купи', 'бесплатно', 'скидка', 'акция', 'срочно', 'заработок',
                  'подарок', 'выигрыш', 'ограниченное предложение', 'только сегодня',
                  'эксклюзивно', 'секрет', 'гарантия', '100%', 'быстро', 'легко']

    # Подсчет восклицательных знаков
    exclamation_count = text.count('!')

    # Подсчет слов в ВЕРХНЕМ регистре
    words = re.findall(r'\b\w+\b', text)
    caps_count = sum(1 for word in words if word.isupper() and len(word) > 1)

    # Подсчет спам-слов
    lower_text = text.lower()
    spam_word_count = sum(1 for word in spam_words if word in lower_text)

    return exclamation_count, caps_count, spam_word_count


def _calculate_sentence_length_variance(text):
    """
    Рассчитывает вариацию длины предложений.
    Высокая вариация обычно указывает на более естественный текст.
    """
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]

    if not sentences:
        return 0

    lengths = [len(s) for s in sentences]
    return np.var(lengths) if len(sentences) > 1 else 0


def _count_filler_words(text):
    """
    Подсчитывает количество слов-паразитов и избыточных конструкций в тексте.
    """
    filler_words = [
        'типа', 'как бы', 'вроде', 'короче', 'вообще', 'в общем-то',
        'так сказать', 'своего рода', 'в некотором роде', 'можно сказать',
        'на самом деле', 'собственно говоря', 'как говорится', 'по сути',
        'безусловно', 'разумеется', 'очевидно', 'как известно', 'в целом'
    ]

    lower_text = text.lower()
    count = sum(lower_text.count(word) for word in filler_words)

    return count


def calculate_spamminess(text):
    """
    Рассчитывает процент спамности текста используя комбинацию методов:
    1. Семантический анализ с помощью предобученной модели
    2. Подсчет спам-маркеров в тексте

    :param text: Анализируемый текст
    :return: Процент спамности (0-100%)
    """
    try:
        model = _get_sentence_transformer_model()

        # Семантический анализ с моделью
        text_embedding = model.encode(text, convert_to_tensor=True, device=model_loader.device)
        spam_embeddings = _get_spam_embeddings()

        # Рассчитываем среднее сходство с примерами спама
        similarities = util.pytorch_cos_sim(text_embedding, spam_embeddings)[0]
        semantic_score = float(similarities.mean()) * 100

        # Анализ спам-маркеров
        exclamation_count, caps_count, spam_word_count = _count_spam_markers(text)

        # Нормализация маркеров (чем больше текст, тем меньше вес единичных маркеров)
        text_length = len(text)
        normalizer = min(1.0, max(0.1, 500 / max(text_length, 1)))

        marker_score = min(100, (exclamation_count * 5 + caps_count * 8 + spam_word_count * 10) * normalizer)

        # Комбинируем оценки (70% семантический анализ, 30% маркеры)
        combined_score = semantic_score * 0.7 + marker_score * 0.3

        # Очищаем кэш GPU после использования
        model_loader.clear_cache()

        return round(combined_score, 2)

    except Exception as e:
        model_loader.logger.error(f"Ошибка при расчете спамности: {e}")
        return 0


def calculate_wateriness(text):
    """
    Рассчитывает процент водянистости текста путем анализа:
    1. Семантического сходства с водянистыми примерами
    2. Вариации длины предложений
    3. Количества слов-паразитов

    :param text: Анализируемый текст
    :return: Процент водянистости (0-100%)
    """
    try:
        # Если текст слишком короткий, считаем его неводянистым
        if len(text) < 100:
            return 0

        model = _get_sentence_transformer_model()

        # Семантический анализ с моделью
        text_embedding = model.encode(text, convert_to_tensor=True, device=model_loader.device)
        watery_embeddings = _get_watery_embeddings()
        normal_embeddings = _get_normal_embeddings()

        # Сходство с водянистыми примерами
        watery_similarities = util.pytorch_cos_sim(text_embedding, watery_embeddings)[0]
        watery_score = float(watery_similarities.mean()) * 100

        # Сходство с нормальными примерами (обратный показатель)
        normal_similarities = util.pytorch_cos_sim(text_embedding, normal_embeddings)[0]
        normal_score = 100 - float(normal_similarities.mean()) * 100

        # Анализ вариации длины предложений (низкая вариация часто указывает на водянистость)
        variance = _calculate_sentence_length_variance(text)
        variance_score = max(0, 100 - min(100, variance / 10))

        # Подсчет слов-паразитов
        filler_count = _count_filler_words(text)
        text_word_count = len(re.findall(r'\b\w+\b', text))
        filler_ratio = filler_count / max(text_word_count, 1)
        filler_score = min(100, filler_ratio * 200)  # Умножаем на 200 для усиления эффекта

        # Комбинируем оценки
        combined_score = (
                watery_score * 0.35 +
                normal_score * 0.25 +
                variance_score * 0.15 +
                filler_score * 0.25
        )

        # Очищаем кэш GPU после использования
        model_loader.clear_cache()

        return round(combined_score, 2)

    except Exception as e:
        model_loader.logger.error(f"Ошибка при расчете водянистости: {e}")
        return 0


def get_seo_diagnostics():
    """Возвращает диагностическую информацию для модуля SEO"""
    try:
        model = model_loader.model
        device_info = model_loader.get_memory_info()

        return {
            "sentence_transformer_loaded": model is not None,
            "device_info": device_info,
            "embeddings_cached": {
                "spam": spam_embeddings is not None,
                "normal": normal_embeddings is not None,
                "watery": watery_embeddings is not None
            },
            "model_device": str(next(model.parameters()).device) if model is not None else "N/A"
        }
    except Exception as e:
        return {
            "error": str(e),
            "sentence_transformer_loaded": False
        }


def clear_embeddings_cache():
    """Очищает кэш эмбеддингов для освобождения памяти"""
    global spam_embeddings, normal_embeddings, watery_embeddings
    spam_embeddings = None
    normal_embeddings = None
    watery_embeddings = None
    model_loader.clear_cache()
    model_loader.logger.info("Кэш эмбеддингов очищен")