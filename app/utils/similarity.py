import numpy as np
import logging
import torch

logging.basicConfig(level=logging.DEBUG)


def calculate_similarity_matrix(uploaded_embeddings, base_embeddings):
    """
    Вычисляет матрицу косинусного сходства между загруженными эмбеддингами и базой.
    :param uploaded_embeddings: список эмбеддингов загруженного текста.
    :param base_embeddings: словарь, где ключ — имя файла, значение — список эмбеддингов.
    :return: матрица сходств в виде numpy массива и список файлов, соответствующих каждому эмбеддингу.
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")  # Определяем, доступна ли CUDA

    # Проверяем, что у нас есть эмбеддинги для обработки
    if not uploaded_embeddings or not base_embeddings:
        return np.array([]), []

    # Создаем список файлов для каждого эмбеддинга
    base_files = []
    base_embeddings_list = []

    for file_name, embeddings in base_embeddings.items():
        for emb in embeddings:
            base_embeddings_list.append(emb)
            base_files.append(file_name)

    # Преобразуем списки эмбеддингов в единые NumPy-массивы перед созданием тензоров
    uploaded_embeddings = np.array(uploaded_embeddings, dtype=np.float32)
    base_embeddings_array = np.array(base_embeddings_list, dtype=np.float32)

    # Проверяем что массивы не пусты
    if uploaded_embeddings.size == 0 or base_embeddings_array.size == 0:
        return np.array([]), []

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

    return similarity_matrix.cpu().numpy(), base_files  # Возвращаем и матрицу, и список файлов


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

    # Получаем матрицу сходства и список файлов, соответствующих каждому эмбеддингу
    similarity_matrix, base_files = calculate_similarity_matrix(uploaded_embeddings, base_embeddings)

    # Проверка на пустую матрицу
    if similarity_matrix.size == 0:
        return 100, {}, [], {}

    # Счетчики для уникальных предложений и заимствований
    unique_count = 0
    file_matches = {}  # словарь для подсчета заимствований по файлам
    matched_sentences = []  # список неуникальных предложений

    # Словарь для хранения детальной информации о сходстве с каждым файлом
    file_similarity_details = {}

    # Инициализируем счетчики заимствований для каждого файла
    for file_name in base_embeddings.keys():
        file_matches[file_name] = 0
        file_similarity_details[file_name] = []

    # Обрабатываем каждое предложение
    for i, row in enumerate(similarity_matrix):
        # Для каждого файла находим максимальное сходство
        file_to_max_similarity = {}

        for j, similarity in enumerate(row):
            file_name = base_files[j]
            similarity_percent = similarity * 100

            # Обновляем максимальное сходство для данного файла, если оно выше
            if file_name not in file_to_max_similarity or similarity_percent > file_to_max_similarity[file_name]:
                file_to_max_similarity[file_name] = similarity_percent

        # Добавляем информацию о максимальном сходстве каждого предложения с каждым файлом
        for file_name, similarity_percent in file_to_max_similarity.items():
            file_similarity_details[file_name].append(similarity_percent)

        # Находим максимальное сходство для текущего предложения среди всех файлов
        max_similarity = max(row) * 100
        if max_similarity > threshold:
            # Находим индекс максимального значения сходства
            max_index = row.argmax()
            # Определяем файл, с которым обнаружено максимальное сходство
            matched_file = base_files[max_index]
            # Увеличиваем счетчик заимствований для этого файла
            file_matches[matched_file] += 1
            # Добавляем предложение в список неуникальных
            matched_sentences.append(sentences[i])
        else:
            # Предложение уникально
            unique_count += 1

    # Вычисляем общую уникальность
    overall_uniqueness = (unique_count / total_sentences) * 100

    # Преобразуем счетчики заимствований в проценты и фильтруем по минимальному порогу
    file_similarity = {}
    for file_name, count in file_matches.items():
        percent = (count / total_sentences) * 100
        if percent >= min_file_similarity:
            file_similarity[file_name] = percent

    # Вычисляем средний процент сходства для каждого файла
    avg_file_similarity = {}
    for file_name, similarities in file_similarity_details.items():
        if similarities:  # Проверка на непустой список
            avg_similarity = sum(similarities) / len(similarities)
            avg_file_similarity[file_name] = avg_similarity

    return overall_uniqueness, file_similarity, matched_sentences, avg_file_similarity