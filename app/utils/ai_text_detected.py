from .model_loader import model_loader
import torch
from tqdm import tqdm
from typing import List, Union

model = model_loader.ai_detector_model
tokenizer = model_loader.ai_detector_tokenizer


def process_text_chunks(text: str, chunk_size: int = 500) -> List[str]:
    """Разбивает текст на чанки по предложениям с учетом максимальной длины."""
    sentences = text.split('. ')
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        if len(current_chunk) + len(sentence) < chunk_size:
            current_chunk += sentence + '. '
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence + '. '

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


def detect_ai_text(text: Union[str, List[str]], batch_size: int = 4, show_progress: bool = True) -> float:
    """
    Определяет вероятность AI-текста (0-100%) с обработкой больших текстов

    Аргументы:
        text: Входной текст или список текстовых чанков
        batch_size: Размер батча для обработки
        show_progress: Показывать прогресс-бар

    Возвращает:
        Среднюю вероятность AI-текста (а не человеческого)
    """
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)

    if isinstance(text, str):
        chunks = process_text_chunks(text)
    else:
        chunks = text

    if not chunks:
        return 0.0  # Пустой текст считаем человеческим (0% AI)

    total_ai_prob = 0.0
    processed_chunks = 0

    progress = tqdm(total=len(chunks), disable=not show_progress, desc="Analyzing text")

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]

        inputs = tokenizer(
            batch,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding="max_length",
            add_special_tokens=True
        ).to(device)

        with torch.no_grad():
            outputs = model(**inputs)
            probs = torch.softmax(outputs.logits, dim=-1)

        # Теперь берем вероятность класса 1 (AI-generated) вместо класса 0
        batch_ai_prob = probs[:, 1].sum().item() * 100
        total_ai_prob += batch_ai_prob
        processed_chunks += len(batch)

        progress.update(len(batch))

    progress.close()

    avg_ai_prob = round(total_ai_prob / processed_chunks, 2)
    return avg_ai_prob


def get_detailed_analysis(text: str) -> dict:
    """
    Возвращает детализированный анализ текста с разбивкой по чанкам

    Возвращает:
        {
            "overall_ai_score": средняя вероятность AI-текста,
            "chunks": [
                {"text": фрагмент, "ai_score": вероятность AI},
                ...
            ],
            "device": используемое устройство
        }
    """
    chunks = process_text_chunks(text)
    device = "cuda" if torch.cuda.is_available() else "cpu"

    results = {
        "overall_ai_score": detect_ai_text(chunks, show_progress=False),
        "chunks": [],
        "device": device
    }

    for chunk in chunks:
        score = detect_ai_text([chunk], batch_size=1, show_progress=False)
        results["chunks"].append({
            "text": chunk,
            "ai_score": score
        })

    return results