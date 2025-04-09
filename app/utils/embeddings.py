import numpy as np
from functools import lru_cache
import spacy
import torch
from sentence_transformers import SentenceTransformer

# Ленивая загрузка моделей
_nlp = None
_model = None

def get_nlp():
    global _nlp
    if _nlp is None:
        _nlp = spacy.load("ru_core_news_lg")
    return _nlp

def get_model():
    global _model
    if _model is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        _model = SentenceTransformer('paraphrase-xlm-r-multilingual-v1').to(device)
    return _model

@lru_cache(maxsize=128)
def preprocess_text_to_embeddings(text: str, language: str) -> list[np.ndarray]:
    """Кэширует эмбеддинги для часто повторяющихся текстов."""
    sentences = [sent.text.strip() for sent in get_nlp()(text).sents]
    return [get_model().encode(sentence) for sentence in sentences]

def load_embeddings_from_file(file_path: str) -> list[np.ndarray]:
    """Оставлено без изменений (кэширование на уровне process_text)."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return [np.array(list(map(float, line.strip().split()))) for line in file]