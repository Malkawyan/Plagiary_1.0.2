import numpy as np
from functools import lru_cache
import spacy
import torch
from sentence_transformers import SentenceTransformer

# Глобальные переменные для ленивой загрузки тяжелых моделей
# Используем паттерн Singleton для предотвращения повторной загрузки
_nlp = None  # Экземпляр модели spaCy для обработки текста
_model = None  # Экземпляр SentenceTransformer для генерации эмбеддингов


def get_nlp():
    """
    Инициализирует и возвращает модель spaCy для русского языка.
    Реализует ленивую загрузку - модель загружается только при первом вызове.

    Returns:
        spacy.Language: Загруженная модель NLP
    """
    global _nlp
    if _nlp is None:
        # Загружаем большую (lg) русскоязычную модель
        _nlp = spacy.load("ru_core_news_lg")
    return _nlp


def get_model():
    """
    Инициализирует и возвращает модель SentenceTransformer.
    Автоматически использует GPU (CUDA) если доступен.

    Returns:
        SentenceTransformer: Модель для генерации эмбеддингов
    """
    global _model
    if _model is None:
        # Определяем доступное вычислительное устройство
        device = "cuda" if torch.cuda.is_available() else "cpu"
        # Загружаем мультиязычную модель для парафразирования
        _model = SentenceTransformer('paraphrase-xlm-r-multilingual-v1').to(device)
    return _model


@lru_cache(maxsize=128)
def preprocess_text_to_embeddings(text: str, language: str) -> list[np.ndarray]:
    """
    Преобразует входной текст в список векторных представлений предложений.
    Использует кэширование результатов для одинаковых входных текстов.

    Args:
        text (str): Исходный текст для обработки
        language (str): Язык текста (не используется в текущей реализации)

    Returns:
        list[np.ndarray]: Список эмбеддингов для каждого предложения в тексте
    """
    # Разбиваем текст на предложения с помощью spaCy
    sentences = [sent.text.strip() for sent in get_nlp()(text).sents]

    # Генерируем эмбеддинги для каждого предложения
    return [get_model().encode(sentence) for sentence in sentences]


def load_embeddings_from_file(file_path: str) -> list[np.ndarray]:
    """
    Загружает эмбеддинги из текстового файла, где каждая строка -
    это вектор чисел, разделенных пробелами.

    Args:
        file_path (str): Путь к файлу с эмбеддингами

    Returns:
        list[np.ndarray]: Список загруженных векторов эмбеддингов

    Пример формата файла:
        0.1 0.2 0.3 ... 0.8
        0.5 0.6 0.1 ... 0.9
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        return [np.array(list(map(float, line.strip().split()))) for line in file]