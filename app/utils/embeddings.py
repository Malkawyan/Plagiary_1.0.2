import numpy as np
from functools import lru_cache
from typing import List, Dict, Union
from .text_utils import split_text_into_sentences, split_text_into_chunks
from .model_loader import model_loader

model = model_loader.model
tokenizer = model_loader.tokenizer


@lru_cache(maxsize=128)
def preprocess_text_to_embeddings(text: str, language: str = "ru") -> List[np.ndarray]:
    """
    Преобразует текст в эмбеддинги, автоматически разбивая длинные тексты.
    """
    max_tokens = 512

    tokens = tokenizer.tokenize(text)
    if len(tokens) <= max_tokens:
        sentences = split_text_into_sentences(text)
        return [model.encode(sentence) for sentence in sentences]

    chunks = split_text_into_chunks(text, max_tokens)
    embeddings = []

    for chunk in chunks:
        chunk_sentences = split_text_into_sentences(chunk)
        embeddings.extend([model.encode(sentence) for sentence in chunk_sentences])

    return embeddings


def load_embeddings_from_file(file_path: str) -> List[np.ndarray]:
    """
    Загружает эмбеддинги из текстового файла.
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        return [np.array(list(map(float, line.strip().split()))) for line in file if line.strip()]


def process_text_with_limits(text: str) -> Dict[str, Union[List[List[float]], Dict[str, int], List[str]]]:
    """
    Обрабатывает текст любого размера с полной информацией о разбиении.
    """
    original_token_count = len(tokenizer.tokenize(text))
    max_tokens = 512
    all_sentences = []

    if original_token_count <= max_tokens:
        sentences = split_text_into_sentences(text)
        all_sentences.extend(sentences)
        embeddings = [model.encode(sentence) for sentence in sentences]
        return {
            "embeddings": [emb.tolist() for emb in embeddings],
            "sentences": all_sentences,
            "processing_info": {
                "total_chunks": 1,
                "total_sentences": len(embeddings),
                "was_truncated": False
            }
        }

    chunks = split_text_into_chunks(text, max_tokens)
    all_embeddings = []

    for chunk in chunks:
        chunk_sentences = split_text_into_sentences(chunk)
        all_sentences.extend(chunk_sentences)
        embeddings = [model.encode(sentence) for sentence in chunk_sentences]
        all_embeddings.extend(embeddings)

    return {
        "embeddings": [emb.tolist() for emb in all_embeddings],
        "sentences": all_sentences,
        "processing_info": {
            "total_chunks": len(chunks),
            "total_sentences": len(all_embeddings),
            "was_truncated": True
        }
    }