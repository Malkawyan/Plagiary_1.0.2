import numpy as np
import logging
import torch
import gc

logging.basicConfig(level=logging.DEBUG)


def _get_device():
    """Определяет оптимальное устройство для вычислений"""
    # Проверяем NVIDIA CUDA
    if torch.cuda.is_available():
        try:
            test_tensor = torch.tensor([1.0]).cuda()
            _ = test_tensor * 2
            return torch.device("cuda")
        except Exception:
            pass

    # Проверяем AMD ROCm
    try:
        import os
        if os.environ.get('ROCM_PATH') or os.environ.get('HIP_PATH'):
            test_tensor = torch.tensor([1.0], device='cuda:0')
            _ = test_tensor * 2
            return torch.device("cuda:0")
    except Exception:
        pass

    return torch.device("cpu")


def calculate_similarity_matrix(uploaded_embeddings, base_embeddings, batch_size=100):
    """
    Вычисляет матрицу косинусного сходства между загруженными эмбеддингами и базой.
    :param uploaded_embeddings: список эмбеддингов загруженного текста.
    :param base_embeddings: словарь, где ключ — имя файла, значение — список эмбеддингов.
    :param batch_size: размер обрабатываемого пакета для экономии памяти
    :return: матрица сходств в виде numpy массива и список файлов, соответствующих каждому эмбеддингу.
    """
    device = _get_device()
    logger = logging.getLogger(__name__)
    logger.info(f"Используется устройство: {device}")

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

    try:
        # Используем float16 для GPU, float32 для CPU
        dtype = torch.float16 if device.type == 'cuda' else torch.float32

        all_base = torch.tensor(base_embeddings_array, device=device, dtype=dtype)

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

            try:
                batch_tensor = torch.tensor(batch, device=device, dtype=dtype)

                norm_batch = torch.norm(batch_tensor, dim=1, keepdim=True)
                norm_batch = torch.clamp(norm_batch, min=1e-8)

                with torch.no_grad():
                    batch_similarity = torch.mm(batch_tensor, all_base.mT) / (norm_batch * norm_all_base)

                similarity_matrix[i:batch_end] = batch_similarity.float().cpu().numpy()

                # Очистка памяти
                del batch_tensor, norm_batch, batch_similarity

                if device.type == 'cuda':
                    torch.cuda.empty_cache()

            except RuntimeError as e:
                if "out of memory" in str(e):
                    logger.warning("Недостаточно GPU памяти, переходим на CPU")
                    if device.type == 'cuda':
                        torch.cuda.empty_cache()
                    # Пересчитываем на CPU
                    return _calculate_on_cpu(uploaded_embeddings, base_embeddings_array, base_files)
                else:
                    raise e

        # Финальная очистка
        del all_base, norm_all_base
        if device.type == 'cuda':
            torch.cuda.empty_cache()
        gc.collect()

        return similarity_matrix, base_files

    except Exception as e:
        logger.error(f"Ошибка GPU вычислений: {e}")
        logger.info("Переходим на CPU")
        return _calculate_on_cpu(uploaded_embeddings, base_embeddings_array, base_files)


def _calculate_on_cpu(uploaded_embeddings, base_embeddings_array, base_files):
    """Простая CPU версия для fallback"""
    logger = logging.getLogger(__name__)
    logger.info("Используется CPU для вычислений")

    # Нормализация
    uploaded_norms = np.linalg.norm(uploaded_embeddings, axis=1, keepdims=True)
    uploaded_norms = np.clip(uploaded_norms, a_min=1e-8, a_max=None)
    uploaded_normalized = uploaded_embeddings / uploaded_norms

    base_norms = np.linalg.norm(base_embeddings_array, axis=1, keepdims=True)
    base_norms = np.clip(base_norms, a_min=1e-8, a_max=None)
    base_normalized = base_embeddings_array / base_norms

    # Косинусное сходство
    similarity_matrix = np.dot(uploaded_normalized, base_normalized.T)

    return similarity_matrix, base_files


def calculate_text_statistics(sentences):
    """
    Вычисляет статистику текста для каждого предложения.
    :param sentences: список предложений
    :return: словарь со статистикой
    """
    stats = {
        'sentence_lengths': [],  # длина каждого предложения в символах
        'sentence_word_counts': [],  # количество слов в каждом предложении
        'total_chars': 0,  # общее количество символов
        'total_words': 0  # общее количество слов
    }

    for sentence in sentences:
        # Убираем лишние пробелы и считаем символы
        clean_sentence = sentence.strip()
        char_count = len(clean_sentence)

        # Считаем слова (разделяем по пробелам и фильтруем пустые)
        words = [word for word in clean_sentence.split() if word.strip()]
        word_count = len(words)

        stats['sentence_lengths'].append(char_count)
        stats['sentence_word_counts'].append(word_count)
        stats['total_chars'] += char_count
        stats['total_words'] += word_count

    return stats


def calculate_uniqueness_and_similarity(uploaded_embeddings, base_embeddings, sentences, threshold=70,
                                        min_file_similarity=1.0):
    """
    Вычисляет общую уникальность текста и проценты заимствования для каждого файла.
    Учитывает объем заимствованного текста, а не только количество предложений.

    :param uploaded_embeddings: список эмбеддингов загруженного текста.
    :param base_embeddings: словарь с эмбеддингами базы (ключ — имя файла, значение — список эмбеддингов).
    :param sentences: список всех предложений загруженного текста.
    :param threshold: порог сходства (в процентах).
    :param min_file_similarity: минимальный процент заимствования из файла, чтобы включить его в результат.
    :return: кортеж (общая уникальность, словарь с процентами заимствования для каждого файла,
             список неуникальных предложений, словарь детальных процентов сходства).
    """
    total_sentences = len(uploaded_embeddings)
    if total_sentences == 0:
        return 100, {}, [], {}

    # Получаем статистику текста
    text_stats = calculate_text_statistics(sentences)

    if text_stats['total_chars'] == 0:
        return 100, {}, [], {}

    similarity_matrix, base_files = calculate_similarity_matrix(uploaded_embeddings, base_embeddings)

    if similarity_matrix.size == 0:
        return 100, {}, [], {}

    # Переменные для подсчета заимствований
    file_borrowed_chars = {}  # количество заимствованных символов по файлам
    file_borrowed_weighted = {}  # взвешенный объем заимствований (учитывает степень сходства)
    matched_sentences = []
    file_similarity_details = {}

    total_borrowed_chars = 0  # общий объем заимствованного текста в символах
    total_borrowed_weighted = 0  # общий взвешенный объем заимствований

    # Инициализируем счетчики для каждого файла
    for file_name in base_embeddings.keys():
        file_borrowed_chars[file_name] = 0
        file_borrowed_weighted[file_name] = 0.0
        file_similarity_details[file_name] = []

    # Обрабатываем каждое предложение
    for i, row in enumerate(similarity_matrix):
        sentence_chars = text_stats['sentence_lengths'][i]

        # Для каждого файла находим максимальное сходство среди его эмбеддингов
        file_to_max_similarity = {}

        for j, similarity in enumerate(row):
            file_name = base_files[j]
            similarity_percent = float(similarity * 100)

            if file_name not in file_to_max_similarity or similarity_percent > file_to_max_similarity[file_name]:
                file_to_max_similarity[file_name] = similarity_percent

        # Сохраняем максимальное сходство с каждым файлом для этого предложения
        for file_name, similarity_percent in file_to_max_similarity.items():
            file_similarity_details[file_name].append(float(similarity_percent))

        # Находим общее максимальное сходство для определения заимствований
        max_similarity = float(max(row) * 100)

        if max_similarity > threshold:
            # Это заимствованное предложение
            max_index = row.argmax()
            matched_file = base_files[max_index]
            matched_sentences.append(sentences[i])

            # Добавляем к общему объему заимствований
            total_borrowed_chars += sentence_chars

            # Взвешенное заимствование учитывает степень сходства
            # Например, предложение с 95% сходством "весит" больше, чем с 71%
            similarity_weight = (max_similarity - threshold) / (100 - threshold)
            weighted_chars = sentence_chars * similarity_weight
            total_borrowed_weighted += weighted_chars

            # Добавляем к файлу-источнику
            file_borrowed_chars[matched_file] += sentence_chars
            file_borrowed_weighted[matched_file] += weighted_chars

    # Вычисляем уникальность на основе объема текста, а не количества предложений
    # Используем взвешенный подход для более точной оценки
    uniqueness_by_chars = ((text_stats['total_chars'] - total_borrowed_chars) / text_stats['total_chars']) * 100
    uniqueness_weighted = ((text_stats['total_chars'] - total_borrowed_weighted) / text_stats['total_chars']) * 100

    # Берем среднее между двумя подходами для более сбалансированной оценки
    overall_uniqueness = (uniqueness_by_chars + uniqueness_weighted) / 2

    # Вычисляем проценты заимствования по файлам
    file_similarity = {}
    avg_file_similarity = {}

    for file_name, similarities in file_similarity_details.items():
        if similarities:
            # Средний процент сходства (для совместимости со старой версией)
            avg_similarity = sum(similarities) / len(similarities)
            avg_file_similarity[file_name] = float(avg_similarity)

            # Новый подход: процент заимствованного текста из этого файла
            if file_borrowed_chars[file_name] > 0:
                # Простой подход: доля символов, заимствованных из файла
                chars_percentage = (file_borrowed_chars[file_name] / text_stats['total_chars']) * 100

                # Взвешенный подход: учитывает степень сходства
                weighted_percentage = (file_borrowed_weighted[file_name] / text_stats['total_chars']) * 100

                # Берем максимум из двух подходов для более консервативной оценки
                final_percentage = max(chars_percentage, weighted_percentage)

                if final_percentage >= min_file_similarity:
                    file_similarity[file_name] = float(final_percentage)

    # Убеждаемся, что значения в допустимых пределах
    overall_uniqueness = max(0.0, min(100.0, float(overall_uniqueness)))

    return overall_uniqueness, file_similarity, matched_sentences, avg_file_similarity