from .model_loader import model_loader
import torch

model = model_loader.ai_detector_model
tokenizer = model_loader.ai_detector_tokenizer


def detect_ai_text(text):
    """Определяет вероятность человеческого текста (0-100%)"""
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)

    # Токенизация с автоматическим padding и truncation
    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        max_length=512,
        padding="max_length"
    ).to(device)

    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.softmax(outputs.logits, dim=-1)

    # Вероятность класса 0 (human-written)
    human_prob_percent = round(probs[0][0].item() * 100, 2)

    return human_prob_percent