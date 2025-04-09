import numpy as np
from functools import lru_cache
from pathlib import Path
from app.utils.embeddings import preprocess_text_to_embeddings, load_embeddings_from_file
from app.utils.similarity import calculate_uniqueness_and_similarity
from app.utils.seo import calculate_spamminess, calculate_wateriness
from app.config import Config


@lru_cache(maxsize=32)
def _get_base_sentences_cache():
    """Кэширует загрузку эмбеддингов из базовой папки."""
    base_sentences = {}
    base_folder_path = Path(Config.BASE_FOLDER)

    if not base_folder_path.exists():
        raise FileNotFoundError("Base folder does not exist")

    for base_file in base_folder_path.iterdir():
        if base_file.is_file():
            base_sentences[base_file.name] = load_embeddings_from_file(base_file)
    return base_sentences


def process_text(text: str, language: str) -> dict:
    """
    Оптимизированная версия с кэшированием загрузки базовых эмбеддингов.
    """
    water_score = calculate_wateriness(text)
    spam_score = calculate_spamminess(text)
    uploaded_embeddings = preprocess_text_to_embeddings(text, language)
    base_sentences = _get_base_sentences_cache()  # Используем кэшированную версию

    overall_uniqueness, file_similarity, matched_indices = calculate_uniqueness_and_similarity(
        uploaded_embeddings, base_sentences
    )

    return {
        "overall_uniqueness": f"{overall_uniqueness:.2f}%",
        "file_similarity": file_similarity,
        "water_score": water_score,
        "spam_score": spam_score,
        "matched_indices": matched_indices
    }