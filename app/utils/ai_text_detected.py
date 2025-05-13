from .model_loader import model_loader
import torch
from tqdm import tqdm
from typing import List, Union, Tuple
import numpy as np
from collections import Counter
import re


def process_text_chunks(text: str, chunk_size: int = 400) -> List[str]:
    """Улучшенное разбиение текста на чанки с сохранением целостности предложений"""
    sentences = []
    current_sentence = []
    current_length = 0

    # Временное разбиение на предложения
    for token in text.split():
        if len(token) + current_length > chunk_size and current_sentence:
            sentences.append(' '.join(current_sentence))
            current_sentence = []
            current_length = 0
        current_sentence.append(token)
        current_length += len(token) + 1

    if current_sentence:
        sentences.append(' '.join(current_sentence))

    return sentences


def calculate_repetition_score(text: str) -> float:
    """Вычисляет оценку повторяемости в тексте (характерно для ИИ)"""
    words = text.lower().split()
    if len(words) < 10:
        return 0.0

    unique_words = set(words)
    return 1 - (len(unique_words) / len(words))


def calculate_perplexity(text: str, model=None, tokenizer=None) -> float:
    """Упрощенная оценка перплексии текста"""
    if not text or len(text.split()) < 5:
        return 0.0

    # Простая эвристика вместо реальной перплексии
    word_variation = len(set(text.split())) / len(text.split())
    sentence_length_variation = np.std([len(sent.split()) for sent in text.split('.') if sent.strip()])

    return word_variation * 0.7 + sentence_length_variation * 0.3


def ensemble_prediction(text: str) -> float:
    """Улучшенное ансамблевое предсказание с калибровкой под современные модели ИИ"""
    models = [
        (model_loader.ai_detector_model, model_loader.ai_detector_tokenizer, 0.5),
        (model_loader.multilingual_detector_model, model_loader.multilingual_detector_tokenizer, 0.3),
        (model_loader.modern_ai_detector_model, model_loader.modern_ai_detector_tokenizer, 0.2)
    ]

    predictions = []
    chunks = process_text_chunks(text)

    for model, tokenizer, weight in models:
        device = next(model.parameters()).device
        chunk_probs = []

        for chunk in chunks:
            inputs = tokenizer(
                chunk,
                return_tensors="pt",
                truncation=True,
                max_length=512,
                padding="max_length"
            ).to(device)

            with torch.no_grad():
                outputs = model(**inputs)
                probs = torch.softmax(outputs.logits, dim=-1)
                calibrated_prob = min(1.0, probs[0][1].item() * 1.3)
                chunk_probs.append(calibrated_prob)

        predictions.append((np.mean(chunk_probs), weight))

    total_weight = sum(w for _, w in predictions)
    combined = sum(p * w for p, w in predictions) / total_weight

    if combined > 0.5:
        combined = min(1.0, combined * 1.2)

    return combined


def analyze_stylistic_features(text: str) -> dict:
    """Улучшенный анализ стилистических особенностей для современных ИИ"""
    if not text:
        return {}

    words = text.split()
    sentences = [s for s in text.split('.') if s.strip()]

    # Базовые метрики
    avg_word_len = sum(len(word) for word in words) / len(words) if words else 0
    avg_sent_len = sum(len(sent.split()) for sent in sentences) / len(sentences) if sentences else 0

    # Счетчик пунктуации
    punct_counts = Counter(c for c in text if not c.isalnum() and not c.isspace())

    # Новые метрики для современных ИИ
    transition_words = ['однако', 'таким образом', 'следовательно', 'в заключение', 'кроме того']
    transition_count = sum(text.lower().count(word) for word in transition_words)

    # Мера "перфектности" текста
    perfect_score = min(1.0, (avg_word_len * 0.1 + avg_sent_len * 0.05 + transition_count * 0.2))

    return {
        "avg_word_length": round(avg_word_len, 2),
        "avg_sentence_length": round(avg_sent_len, 2),
        "punctuation_distribution": dict(punct_counts.most_common(5)),
        "word_diversity": len(set(words)) / len(words) if words else 0,
        "transition_words_count": transition_count,
        "perfectness_score": round(perfect_score, 2),
        "ai_style_markers": {
            "repetition_score": calculate_repetition_score(text),
            "perplexity": calculate_perplexity(text)
        }
    }


def detect_ai_text(text: Union[str, List[str]], batch_size: int = 4, show_progress: bool = True) -> float:
    """Улучшенная функция детекции с калибровкой для современных ИИ"""
    if not text:
        return 0.0

    if isinstance(text, str):
        raw_score = ensemble_prediction(text)
        calibrated_score = raw_score * 1.25 if raw_score > 0.4 else raw_score
        return min(100, calibrated_score * 100)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = model_loader.modern_ai_detector_model
    tokenizer = model_loader.modern_ai_detector_tokenizer
    model.to(device)

    total_ai_prob = 0.0
    processed_chunks = 0

    progress = tqdm(total=len(text), disable=not show_progress, desc="Analyzing text")

    for i in range(0, len(text), batch_size):
        batch = text[i:i + batch_size]

        inputs = tokenizer(
            batch,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding="max_length"
        ).to(device)

        with torch.no_grad():
            outputs = model(**inputs)
            probs = torch.softmax(outputs.logits, dim=-1)
            batch_ai_prob = probs[:, 1].sum().item() * 100

        total_ai_prob += batch_ai_prob
        processed_chunks += len(batch)
        progress.update(len(batch))

    progress.close()
    return round(total_ai_prob / processed_chunks, 2)


def get_detailed_analysis(text: str) -> dict:
    """Детализированный анализ с разбивкой по чанкам и стилистическими маркерами"""
    chunks = process_text_chunks(text)
    device = "cuda" if torch.cuda.is_available() else "cpu"

    # Основные метрики
    ai_score = detect_ai_text(chunks, show_progress=False)
    stylistic_features = analyze_stylistic_features(text)

    results = {
        "overall_ai_score": ai_score,
        "chunks": [],
        "stylistic_features": stylistic_features,
        "device": device
    }

    # Анализ по чанкам
    for chunk in chunks:
        score = detect_ai_text([chunk], batch_size=1, show_progress=False)
        results["chunks"].append({
            "text": chunk,
            "ai_score": score,
            "features": analyze_stylistic_features(chunk)
        })

    return results