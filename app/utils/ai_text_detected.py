from transformers import AutoTokenizer, AutoModelForSequenceClassification
from .model_loader import model_loader
import torch

model = model_loader.ai_detector_model
tokenizer = model_loader.ai_detector_tokenizer

def detect_ai_text(text):
    device = "cuda" if torch.cuda.is_available() else "cpu"  # Выбор устройства
    model.to(device)

    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
    inputs = {key: value.to(device) for key, value in inputs.items()}  # Перемещаем все тензоры на устройство

    outputs = model(**inputs)
    probs = torch.softmax(outputs.logits, dim=-1)
    ai_prob_percent = round(probs[0][1].item() * 100, 2)
    return ai_prob_percent