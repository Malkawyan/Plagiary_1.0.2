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

# def calculate_uniqueness(uploaded_embeddings, base_embeddings):
#     """
#     Вычисляет процент уникальности текста, сравнивая его предложения с базой.
#     """
#     logging.info(f"Начинаем вычисление уникальности для {len(uploaded_embeddings)} предложений.")
#
#     if len(uploaded_embeddings) == 0:
#         logging.error("Ошибка: Нет предложений в загруженном тексте.")
#         return 0
#
#     matched_sentences = 0
#     for emb1 in uploaded_embeddings:
#         sentence_matched = False
#         for emb2 in base_embeddings:
#             similarity = calculate_similarity(emb1, emb2)
#             logging.debug(f"Сходство: {similarity}% между предложением и базой.")
#             if similarity > 80:  # Если сходство > 80%, считаем совпадением
#                 sentence_matched = True
#                 break
#         if sentence_matched:
#             matched_sentences += 1
#
#     total_sentences = len(uploaded_embeddings)  # Общее количество предложений в тексте
#     if total_sentences == 0:
#         logging.error("Ошибка: Общее количество предложений равно 0.")
#         return 0
#
#     uniqueness = ((total_sentences - matched_sentences) / total_sentences) * 100  # Уникальность в процентах
#
#     logging.info(f"Уникальность: {uniqueness}% для {total_sentences} предложений")
#     return uniqueness

def calculate_uniqueness_and_similarity(uploaded_embeddings, base_embeddings):
    """
    Вычисляет общую уникальность и проценты заимствования для каждого файла.

    :param uploaded_embeddings: Эмбеддинги загруженного текста.
    :param base_embeddings: Словарь, где ключ — имя файла, значение — список эмбеддингов.
    :return: Кортеж (общая уникальность, словарь с процентами заимствования для каждого файла).
    """
    total_sentences = len(uploaded_embeddings)
    if total_sentences == 0:
        return 100, {}  # Если предложений нет, считаем текст полностью уникальным

    unique_sentences = 0
    file_similarity = {file_name: 0 for file_name in base_embeddings.keys()}  # Инициализируем словарь

    for emb1 in uploaded_embeddings:
        match_found = False
        for file_name, embeddings in base_embeddings.items():
            for emb2 in embeddings:
                similarity = calculate_similarity(emb1, emb2)
                if similarity > 80:  # Если сходство > 80%, считаем совпадением
                    match_found = True
                    file_similarity[file_name] += 1  # Увеличиваем счетчик заимствований для файла
                    break
            if match_found:
                break

        if not match_found:
            unique_sentences += 1

    # Вычисляем общую уникальность
    overall_uniqueness = (unique_sentences / total_sentences) * 100

    # Вычисляем проценты заимствования для каждого файла
    for file_name, matched_sentences in file_similarity.items():
        file_similarity[file_name] = (matched_sentences / total_sentences) * 100

    # Фильтруем файлы с заимствованием > n%
    file_similarity = {file: similarity for file, similarity in file_similarity.items() if similarity > 1}

    return overall_uniqueness, file_similarity