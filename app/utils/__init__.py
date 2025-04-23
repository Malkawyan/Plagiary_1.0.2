from .embeddings import preprocess_text_to_embeddings, load_embeddings_from_file
from .similarity import calculate_similarity_matrix, calculate_uniqueness_and_similarity
from .seo import calculate_spamminess, calculate_wateriness
from .ai_text_detected import detect_ai_text
from .text_utils import split_text_into_sentences, split_text_into_chunks

# Экспортируем функции для удобного импорта
__all__ = [
    "preprocess_text_to_embeddings",
    "load_embeddings_from_file",
    "calculate_similarity_matrix",
    "calculate_uniqueness_and_similarity",
    "calculate_spamminess",
    "calculate_wateriness",
    "detect_ai_text"
]