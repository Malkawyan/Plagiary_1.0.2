from .model_loader import model_loader
import torch
from tqdm import tqdm
from typing import List, Union
import numpy as np
import re


def calculate_russian_ai_patterns(text: str) -> float:
    """Детекция паттернов, характерных для русского AI-текста"""
    if not text or len(text.split()) < 5:
        return 0.0

    ai_patterns = 0
    text_lower = text.lower()

    # Расширенные AI-фразы на русском (современные GPT модели)
    ai_phrases = [
        'важно отметить', 'стоит отметить', 'следует отметить', 'необходимо отметить',
        'таким образом', 'в заключение', 'подводя итог', 'в итоге', 'резюмируя',
        'кроме того', 'более того', 'помимо этого', 'дополнительно',
        'с одной стороны', 'с другой стороны', 'в то же время',
        'необходимо подчеркнуть', 'нельзя не отметить', 'стоит подчеркнуть',
        'однако', 'тем не менее', 'несмотря на это',
        'в первую очередь', 'прежде всего', 'главным образом',
        'что касается', 'относительно', 'в отношении',
        'безусловно', 'несомненно', 'определенно', 'очевидно'
    ]

    # Подсчет фраз с весами
    phrase_count = 0
    for phrase in ai_phrases:
        count = text_lower.count(phrase)
        phrase_count += count
        if count > 0:
            ai_patterns += count * 2  # Увеличиваем вес

    # Структурные паттерны
    sentences = [s.strip() for s in text.split('.') if s.strip() and len(s.strip()) > 5]

    if len(sentences) > 2:
        # Слишком правильная длина предложений
        lengths = [len(s.split()) for s in sentences]
        avg_length = sum(lengths) / len(lengths)

        # Современные AI делают предложения 8-25 слов
        if 8 <= avg_length <= 25:
            ai_patterns += 3

        # Слишком равномерная длина предложений
        if len(lengths) > 3:
            variance = np.var(lengths)
            if variance < 20:  # Низкая вариативность длины
                ai_patterns += 2

    # Слишком много списков и структурированности
    list_markers = text.lower().count('во-первых') + text.lower().count('во-вторых') + text.lower().count('в-третьих')
    if list_markers > 0:
        ai_patterns += list_markers * 2

    # Избыточная вежливость и формальность
    formal_phrases = ['позвольте', 'разрешите', 'хотелось бы отметить', 'важно понимать']
    for phrase in formal_phrases:
        ai_patterns += text_lower.count(phrase) * 3

    # Нормализуем относительно длины текста
    word_count = len(text.split())
    normalized_score = ai_patterns / max(1, word_count / 50)  # Более чувствительная нормализация

    return min(1.0, normalized_score)


def detect_ai_text_improved(text: str) -> float:
    """Улучшенная детекция AI для русского языка"""
    if not text or len(text.split()) < 10:
        return 0.0

    # Сначала проверяем паттерны
    pattern_score = calculate_russian_ai_patterns(text)

    # Если паттернов много, сразу высокий скор
    if pattern_score > 0.3:
        base_score = pattern_score
    else:
        base_score = pattern_score * 0.5

    # Дополнительные эвристики для современных моделей

    # 1. Слишком "правильный" русский язык
    words = text.split()
    if len(words) > 50:
        # Проверяем разнообразие слов
        unique_words = len(set(words))
        diversity = unique_words / len(words)

        # AI генерирует менее разнообразный текст
        if diversity < 0.6:
            base_score += 0.2

    # 2. Типичные AI-конструкции в русском
    ai_constructions = [
        r'что\s+позволяет',
        r'что\s+способствует',
        r'это\s+означает',
        r'данный\s+подход',
        r'указанный\s+метод',
        r'рассматриваемый\s+вопрос'
    ]

    construction_count = 0
    for pattern in ai_constructions:
        construction_count += len(re.findall(pattern, text.lower()))

    if construction_count > 0:
        base_score += min(0.3, construction_count * 0.1)

    # 3. Слишком много причастных оборотов (AI любит их)
    participle_patterns = [r'\w+ющий', r'\w+ащий', r'\w+вший', r'\w+нный']
    participle_count = 0
    for pattern in participle_patterns:
        participle_count += len(re.findall(pattern, text.lower()))

    if participle_count > len(words) / 20:  # Слишком много причастий
        base_score += 0.15

    # Пытаемся использовать модель, если доступна
    model = model_loader.ai_detector_model
    tokenizer = model_loader.ai_detector_tokenizer

    if model is not None and tokenizer is not None:
        try:
            # Берем первые 400 слов для анализа
            chunk_words = text.split()[:400]
            chunk = ' '.join(chunk_words)

            inputs = tokenizer(
                chunk,
                return_tensors="pt",
                truncation=True,
                max_length=512,
                padding=True
            ).to(model_loader.device)

            with torch.no_grad():
                outputs = model(**inputs)
                probs = torch.softmax(outputs.logits, dim=-1)

                # Пробуем разные индексы для AI класса
                if probs.shape[1] >= 2:
                    ai_prob = max(probs[0][1].item(), probs[0][0].item())
                else:
                    ai_prob = probs[0][0].item()

                # Комбинируем с эвристиками (больший вес эвристикам для русского)
                final_score = base_score * 0.8 + ai_prob * 0.2

        except Exception as e:
            model_loader.logger.error(f"Ошибка модели: {e}")
            final_score = base_score
    else:
        final_score = base_score

    # Калибровка для современных моделей
    if final_score > 0.2:
        final_score = min(1.0, final_score * 1.5)  # Более агрессивная калибровка

    model_loader.clear_cache()
    return round(final_score * 100, 2)


def get_detailed_ai_analysis(text: str) -> dict:
    """Детальный анализ с разбивкой по фрагментам"""
    if not text:
        return {"overall_ai_score": 0.0, "chunks": [], "error": "Пустой текст"}

    # Разбиваем на абзацы, а не предложения
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]

    if not paragraphs:
        # Fallback на предложения
        sentences = [s.strip() + '.' for s in text.split('.') if s.strip()]
        if len(sentences) < 2:
            overall_score = detect_ai_text_improved(text)
            return {
                "overall_ai_score": overall_score,
                "chunks": [{
                    "chunk_id": 1,
                    "text": text[:200] + "..." if len(text) > 200 else text,
                    "ai_score": overall_score
                }]
            }
        chunks = [' '.join(sentences[i:i + 3]) for i in range(0, len(sentences), 3)]
    else:
        chunks = paragraphs

    chunk_results = []
    chunk_scores = []

    for i, chunk in enumerate(chunks):
        if len(chunk.split()) < 5:  # Пропускаем слишком короткие
            continue

        score = detect_ai_text_improved(chunk)
        chunk_scores.append(score)

        chunk_results.append({
            "chunk_id": i + 1,
            "text": chunk[:200] + "..." if len(chunk) > 200 else chunk,
            "full_text_length": len(chunk),
            "ai_score": score
        })

    overall_score = np.mean(chunk_scores) if chunk_scores else 0.0

    # Дополнительный анализ всего текста
    full_text_score = detect_ai_text_improved(text)

    # Берем максимум из средней оценки чанков и оценки всего текста
    final_score = max(overall_score, full_text_score)

    return {
        "overall_ai_score": round(final_score, 2),
        "chunks": chunk_results,
        "stylistic_features": {
            "transition_words_count": len(
                re.findall(r'таким образом|в заключение|кроме того|однако|тем не менее', text.lower())),
            "ai_phrases_detected": calculate_russian_ai_patterns(text) > 0.2,
            "formal_style_score": len(re.findall(r'необходимо|следует|важно отметить|стоит подчеркнуть', text.lower())),
            "structure_regularity": "high" if len(text.split('.')) > 3 else "normal"
        }
    }


# Основные функции для совместимости
def detect_ai_text(text: Union[str, List[str]], **kwargs) -> float:
    """Основная функция детекции - совместимость с существующим кодом"""
    if isinstance(text, list):
        scores = [detect_ai_text_improved(t) for t in text if t and t.strip()]
        return np.mean(scores) if scores else 0.0
    return detect_ai_text_improved(text)


def get_detailed_analysis(text: str) -> dict:
    """Обновленная функция детального анализа"""
    return get_detailed_ai_analysis(text)