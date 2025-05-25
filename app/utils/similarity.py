import numpy as np
import logging
import torch

logging.basicConfig(level=logging.DEBUG)


def calculate_similarity_matrix(uploaded_embeddings, base_embeddings, batch_size=100):
    """
    Вычисляет матрицу косинусного сходства между загруженными эмбеддингами и базой.
    :param uploaded_embeddings: список эмбеддингов загруженного текста.
    :param base_embeddings: словарь, где ключ — имя файла, значение — список эмбеддингов.
    :param batch_size: размер обрабатываемого пакета для экономии памяти
    :return: матрица сходств в виде numpy массива и список файлов, соответствующих каждому эмбеддингу.
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    if not uploaded_embeddings or not base_embeddings:
        return np.array([]), []

    base_files = []
    base_embeddings_list = []

    for file_name, embeddings in base_embeddings.items():
        for emb in embeddings:
            base_embeddings_list.append(emb)
            base_files.append(file_name)

    uploaded_embeddings = np.array(uploaded_embeddings, dtype=np.float32)
    base_embeddings_array = np.array(base_embeddings_list, dtype=np.float32)

    if uploaded_embeddings.size == 0 or base_embeddings_array.size == 0:
        return np.array([]), []

    all_base = torch.tensor(base_embeddings_array, device=device)

    if len(uploaded_embeddings.shape) == 1:
        uploaded_embeddings = uploaded_embeddings.reshape(1, -1)

    if len(all_base.shape) == 1:
        all_base = all_base.unsqueeze(0)

    norm_all_base = torch.norm(all_base, dim=1)
    norm_all_base = torch.clamp(norm_all_base, min=1e-8)

    num_uploaded = len(uploaded_embeddings)
    num_base = len(base_embeddings_list)
    similarity_matrix = np.zeros((num_uploaded, num_base), dtype=np.float32)

    for i in range(0, num_uploaded, batch_size):
        batch_end = min(i + batch_size, num_uploaded)
        batch = uploaded_embeddings[i:batch_end]

        batch_tensor = torch.tensor(batch, device=device)

        norm_batch = torch.norm(batch_tensor, dim=1, keepdim=True)
        norm_batch = torch.clamp(norm_batch, min=1e-8)

        batch_similarity = torch.mm(batch_tensor, all_base.mT) / (norm_batch * norm_all_base)

        similarity_matrix[i:batch_end] = batch_similarity.cpu().numpy()

        if device.type == 'cuda':
            torch.cuda.empty_cache()

    return similarity_matrix, base_files


def calculate_uniqueness_and_similarity(uploaded_embeddings, base_embeddings, sentences, threshold=70,
                                        min_file_similarity=1.0):
    """
    Вычисляет общую уникальность текста и проценты заимствования для каждого файла.
    :param uploaded_embeddings: список эмбеддингов загруженного текста.
    :param base_embeddings: словарь с эмбеддингами базы (ключ — имя файла, значение — список эмбеддингов).
    :param sentences: список всех предложений загруженного текста.
    :param threshold: порог сходства (в процентах).
    :param min_file_similarity: минимальный процент заимствования из файла, чтобы включить его в результат (по умолчанию 1%).
    :return: кортеж (общая уникальность, словарь с процентами заимствования для каждого файла,
             список неуникальных предложений, словарь детальных процентов сходства).
    """
    total_sentences = len(uploaded_embeddings)
    if total_sentences == 0:
        return 100, {}, [], {}

    similarity_matrix, base_files = calculate_similarity_matrix(uploaded_embeddings, base_embeddings)

    if similarity_matrix.size == 0:
        return 100, {}, [], {}

    unique_count = 0
    file_matches = {}  # счетчик заимствований по файлам
    matched_sentences = []
    file_similarity_details = {}

    # Инициализируем счетчики для каждого файла
    for file_name in base_embeddings.keys():
        file_matches[file_name] = 0
        file_similarity_details[file_name] = []

    # Обрабатываем каждое предложение
    for i, row in enumerate(similarity_matrix):
        # Для каждого файла находим максимальное сходство среди его эмбеддингов
        file_to_max_similarity = {}

        for j, similarity in enumerate(row):
            file_name = base_files[j]
            # Преобразуем в стандартный Python float
            similarity_percent = float(similarity * 100)

            if file_name not in file_to_max_similarity or similarity_percent > file_to_max_similarity[file_name]:
                file_to_max_similarity[file_name] = similarity_percent

        # Сохраняем максимальное сходство с каждым файлом для этого предложения
        for file_name, similarity_percent in file_to_max_similarity.items():
            # Преобразуем в стандартный Python float
            file_similarity_details[file_name].append(float(similarity_percent))

        # Находим общее максимальное сходство для определения уникальности
        max_similarity = float(max(row) * 100)
        if max_similarity > threshold:
            max_index = row.argmax()
            matched_file = base_files[max_index]
            file_matches[matched_file] += 1
            matched_sentences.append(sentences[i])
        else:
            unique_count += 1

    # Вычисляем общую уникальность
    overall_uniqueness = (unique_count / total_sentences) * 100

    # ИСПРАВЛЕНИЕ: Вычисляем среднее сходство для каждого файла вместо доли предложений
    file_similarity = {}
    avg_file_similarity = {}

    for file_name, similarities in file_similarity_details.items():
        if similarities:
            # Средний процент сходства со всеми предложениями
            avg_similarity = sum(similarities) / len(similarities)
            # Преобразуем в стандартный Python float для JSON сериализации
            avg_similarity = float(avg_similarity)
            avg_file_similarity[file_name] = avg_similarity

            # Для file_similarity используем среднее сходство, если оно превышает порог
            if avg_similarity >= min_file_similarity:
                file_similarity[file_name] = avg_similarity

    # Убеждаемся, что overall_uniqueness тоже стандартный Python тип
    overall_uniqueness = float(overall_uniqueness)

    return overall_uniqueness, file_similarity, matched_sentences, avg_file_similarity