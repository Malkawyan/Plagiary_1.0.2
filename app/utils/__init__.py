from .embeddings import preprocess_text_to_embeddings, load_embeddings_from_file
from .similarity import calculate_similarity, calculate_uniqueness_and_similarity

# Экспортируем функции для удобного импорта
__all__ = [
    "preprocess_text_to_embeddings",
    "load_embeddings_from_file",
    "calculate_similarity",
    #"calculate_uniqueness",
    "calculate_uniqueness_and_similarity",
]