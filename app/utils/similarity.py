import numpy as np
import logging
import torch

logging.basicConfig(level=logging.DEBUG)


def calculate_similarity_matrix(uploaded_embeddings, base_embeddings):
    """
    Вычисляет матрицу косинусного сходства между загруженными эмбеддингами и базой.
    :param uploaded_embeddings: список эмбеддингов загруженного текста.
    :param base_embeddings: словарь, где ключ — имя файла, значение — список эмбеддингов.
    :return: матрица сходств в виде numpy массива.
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")  # Определяем, доступна ли CUDA

    # Проверяем, что у нас есть эмбеддинги для обработки
    if not uploaded_embeddings or not base_embeddings:
        return np.array([])

    # Преобразуем списки эмбеддингов в единые NumPy-массивы перед созданием тензоров
    uploaded_embeddings = np.array(uploaded_embeddings, dtype=np.float32)
    base_embeddings_list = [emb for embeddings in base_embeddings.values() for emb in embeddings]
    base_embeddings_array = np.array(base_embeddings_list, dtype=np.float32)

    # Проверяем что массивы не пусты
    if uploaded_embeddings.size == 0 or base_embeddings_array.size == 0:
        return np.array([])

    # Создаём тензоры PyTorch и перемещаем на устройство (GPU, если доступен)
    uploaded = torch.tensor(uploaded_embeddings, device=device)
    all_base = torch.tensor(base_embeddings_array, device=device)

    # Убедимся, что тензоры имеют правильную форму для матричного умножения
    if len(uploaded.shape) == 1:
        uploaded = uploaded.unsqueeze(0)  # Добавляем размерность, если у нас один вектор

    if len(all_base.shape) == 1:
        all_base = all_base.unsqueeze(0)

    # Вычисляем косинусное сходство через матричное умножение
    # Используем матричное транспонирование с mT вместо T
    norm_uploaded = torch.norm(uploaded, dim=1, keepdim=True)
    norm_all_base = torch.norm(all_base, dim=1)

    # Избегаем деления на ноль
    norm_uploaded = torch.clamp(norm_uploaded, min=1e-8)
    norm_all_base = torch.clamp(norm_all_base, min=1e-8)

    similarity_matrix = torch.mm(uploaded, all_base.mT) / (
            norm_uploaded * norm_all_base
    )

    return similarity_matrix.cpu().numpy()  # Переносим обратно на CPU для дальнейшей обработки


def calculate_uniqueness_and_similarity(uploaded_embeddings, base_embeddings, sentences, threshold=70):
    """
    Вычисляет общую уникальность текста и проценты заимствования для каждого файла.
    :param uploaded_embeddings: список эмбеддингов загруженного текста.
    :param base_embeddings: словарь с эмбеддингами базы (ключ — имя файла, значение — список эмбеддингов).
    :param sentences: список всех предложений загруженного текста.
    :param threshold: порог сходства (по умолчанию 80%).
    :return: кортеж (общая уникальность, словарь с процентами заимствования для каждого файла, список неуникальных предложений).
    """
    total_sentences = len(uploaded_embeddings)
    if total_sentences == 0:
        return 100, {}, []

    similarity_matrix = calculate_similarity_matrix(uploaded_embeddings, base_embeddings)

    # Проверка на пустую матрицу
    if similarity_matrix.size == 0:
        return 100, {}, []

    unique_sentences = 0
    file_similarity = {file_name: 0 for file_name in base_embeddings.keys()}
    matched_sentences = []

    base_files = [file for file, embeddings in base_embeddings.items() for _ in embeddings]

    for i, row in enumerate(similarity_matrix):
        max_similarity = max(row) * 100
        if max_similarity > threshold:
            file_similarity[base_files[row.argmax()]] += 1
            matched_sentences.append(sentences[i])
        else:
            unique_sentences += 1

    overall_uniqueness = (unique_sentences / total_sentences) * 100

    for file_name in file_similarity:
        file_similarity[file_name] = (file_similarity[file_name] / total_sentences) * 100

    file_similarity = {file: sim for file, sim in file_similarity.items() if sim > 1}

    return overall_uniqueness, file_similarity, matched_sentences