from sentence_transformers import SentenceTransformer, util
import torch

# Загружаем предобученную модель
device = "cuda" if torch.cuda.is_available() else "cpu"
model = SentenceTransformer('paraphrase-xlm-r-multilingual-v1').to(device)

# Эталонные примеры
normal_text = "Это обычный информативный текст без лишних слов и повторов."
spam_text = "Купи сейчас! Супер скидки! Бесплатно! Волшебный метод! Успей!"

def calculate_spamminess(text):
    """
    Рассчитывает процент спамности текста путем сравнения с эталонным спам-текстом.
    :param text: Анализируемый текст.
    :return: Процент спамности (0-100%).
    """
    try:
        text_embedding = model.encode(text, convert_to_tensor=True)
        spam_embedding = model.encode(spam_text, convert_to_tensor=True)
        similarity = util.pytorch_cos_sim(text_embedding, spam_embedding).item()
        return round(similarity * 100, 2)  # В процентах
    except Exception as e:
        print(f"Ошибка при расчете спамности: {e}")
        return 0

def calculate_wateriness(text):
    """
    Рассчитывает процент водянистости текста путем сравнения с эталонным нормальным текстом.
    :param text: Анализируемый текст.
    :return: Процент водянистости (0-100%).
    """
    try:
        text_embedding = model.encode(text, convert_to_tensor=True)
        normal_embedding = model.encode(normal_text, convert_to_tensor=True)
        similarity = util.pytorch_cos_sim(text_embedding, normal_embedding).item()
        return round((1 - similarity) * 100, 2)  # Чем выше, тем больше воды
    except Exception as e:
        print(f"Ошибка при расчете водянистости: {e}")
        return 0