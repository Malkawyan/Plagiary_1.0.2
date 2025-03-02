import numpy as np
from sentence_transformers import SentenceTransformer
import spacy
import torch

# Загрузка языковой модели spaCy для предварительной обработки текста
nlp = spacy.load("ru_core_news_lg")
# Модель SentenceTransformer для генерации эмбеддингов
device = "cuda" if torch.cuda.is_available() else "cpu"
model = SentenceTransformer('paraphrase-xlm-r-multilingual-v1').to(device)

def preprocess_text_to_embeddings(text, language):
    """
    Выполняет разделение текста на предложения и преобразует каждое предложение в эмбеддинг.

    :param text: Текст, который нужно обработать
    :param language: Язык текста (например, 'ru', 'en')
    :return: Список эмбеддингов предложений
    """
    sentences = [sent.text.strip() for sent in nlp(text).sents]  # Разделяем текст на предложения
    return [model.encode(sentence) for sentence in sentences]  # Преобразуем каждое предложение в эмбеддинг

def load_embeddings_from_file(file_path):
    """
    Загружает эмбеддинги из файла.

    :param file_path: Путь к текстовому файлу с эмбеддингами
    :return: Список эмбеддингов (векторных представлений предложений)
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        return [np.array(list(map(float, line.strip().split()))) for line in file]