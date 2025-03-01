import numpy as np
import logging

logging.basicConfig(level=logging.DEBUG)

def calculate_similarity(embedding1, embedding2):
    """
    Вычисляет косинусное сходство между двумя эмбеддингами.
    """
    cosine_similarity = np.dot(embedding1, embedding2) / (np.linalg.norm(embedding1) * np.linalg.norm(embedding2))
    similarity_percentage = max(0, min(cosine_similarity * 100, 100))  # Ограничиваем результат от 0 до 100%
    return similarity_percentage

def calculate_uniqueness(uploaded_embeddings, base_embeddings):
    """
    Вычисляет процент уникальности текста, сравнивая его предложения с базой.
    """
    logging.info(f"Начинаем вычисление уникальности для {len(uploaded_embeddings)} предложений.")

    if len(uploaded_embeddings) == 0:
        logging.error("Ошибка: Нет предложений в загруженном тексте.")
        return 0

    matched_sentences = 0
    for emb1 in uploaded_embeddings:
        sentence_matched = False
        for emb2 in base_embeddings:
            similarity = calculate_similarity(emb1, emb2)
            logging.debug(f"Сходство: {similarity}% между предложением и базой.")
            if similarity > 80:  # Если сходство > 80%, считаем совпадением
                sentence_matched = True
                break
        if sentence_matched:
            matched_sentences += 1

    total_sentences = len(uploaded_embeddings)  # Общее количество предложений в тексте
    if total_sentences == 0:
        logging.error("Ошибка: Общее количество предложений равно 0.")
        return 0

    uniqueness = ((total_sentences - matched_sentences) / total_sentences) * 100  # Уникальность в процентах

    logging.info(f"Уникальность: {uniqueness}% для {total_sentences} предложений")
    return uniqueness