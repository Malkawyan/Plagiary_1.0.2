import os
import json
import logging
import re
import shutil

# Пути к папкам
UPLOADS_DIR = '../uploads'
BACKUP_DIR = '../backup'
CONFIG_FILE = '../app/utils/config.json'
SIMILARITY_FILE = '../app/utils/similarity.py'

# Значения по умолчанию
DEFAULT_THRESHOLD = 60

def load_settings():
    """Загружает настройки из конфигурационного файла"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Ошибка при загрузке настроек: {e}")

    return {"threshold": DEFAULT_THRESHOLD}

def save_settings(settings):
    """Сохраняет настройки в конфигурационный файл"""
    try:
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, 'w') as f:
            json.dump(settings, f)
        logging.info(f"Настройки сохранены: {settings}")
        return True
    except Exception as e:
        logging.error(f"Ошибка при сохранении настроек: {e}")
        return False

def update_similarity_threshold(threshold):
    """Обновляет значение порога в файле similarity.py"""
    try:
        if os.path.exists(SIMILARITY_FILE):
            with open(SIMILARITY_FILE, 'r', encoding='utf-8') as f:
                content = f.read()

            pattern = r'def calculate_uniqueness_and_similarity\(.*?threshold=(\d+)'
            match = re.search(pattern, content, re.DOTALL)

            if match:
                current_threshold = match.group(1)
                new_content = content.replace(
                    f"def calculate_uniqueness_and_similarity(uploaded_embeddings, base_embeddings, sentences, threshold={current_threshold}",
                    f"def calculate_uniqueness_and_similarity(uploaded_embeddings, base_embeddings, sentences, threshold={threshold}"
                )

                with open(SIMILARITY_FILE, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                logging.info(f"Порог обновлен: {current_threshold} -> {threshold}")
            else:
                logging.warning("Не найден параметр threshold в similarity.py")
                return False
        else:
            os.makedirs(os.path.dirname(SIMILARITY_FILE), exist_ok=True)
            with open('similarity.py', 'r', encoding='utf-8') as source:
                content = source.read()

            pattern = r'def calculate_uniqueness_and_similarity\(.*?threshold=(\d+)'
            match = re.search(pattern, content, re.DOTALL)

            if match:
                current_threshold = match.group(1)
                new_content = content.replace(
                    f"def calculate_uniqueness_and_similarity(uploaded_embeddings, base_embeddings, sentences, threshold={current_threshold}",
                    f"def calculate_uniqueness_and_similarity(uploaded_embeddings, base_embeddings, sentences, threshold={threshold}"
                )

                with open(SIMILARITY_FILE, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                logging.info(f"Создан similarity.py с порогом: {threshold}")
            else:
                shutil.copy2('similarity.py', SIMILARITY_FILE)
                logging.info("Файл similarity.py скопирован без изменений")

        return True
    except Exception as e:
        logging.error(f"Ошибка при обновлении порога: {e}", exc_info=True)
        return False