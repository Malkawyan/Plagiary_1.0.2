import spacy
import torch
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from typing import Optional


class ModelLoader:
    """
    Класс для ленивой загрузки и хранения NLP моделей
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._nlp = None
            cls._instance._model = None
            cls._instance._tokenizer = None
            cls._instance._ai_detector_model = None
            cls._instance._ai_detector_tokenizer = None

            # Добавляем модели для определения ChatGPT-4
            cls._instance._chatgpt4_detector_model = None
            cls._instance._chatgpt4_detector_tokenizer = None

            # Добавляем модели для определения DeepSeek
            cls._instance._deepseek_detector_model = None
            cls._instance._deepseek_detector_tokenizer = None
        return cls._instance

    @property
    def nlp(self) -> spacy.Language:
        """Инициализирует и возвращает модель spaCy для русского языка."""
        if self._nlp is None:
            self._nlp = spacy.load("ru_core_news_lg")
        return self._nlp

    @property
    def model(self) -> SentenceTransformer:
        """Инициализирует и возвращает модель SentenceTransformer."""
        if self._model is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
            self._model = SentenceTransformer(
                'paraphrase-xlm-r-multilingual-v1'
            ).to(device)
        return self._model

    @property
    def tokenizer(self) -> AutoTokenizer:
        """Инициализирует и возвращает токенизатор для модели."""
        if self._tokenizer is None:
            self._tokenizer = AutoTokenizer.from_pretrained(
                'sentence-transformers/paraphrase-xlm-r-multilingual-v1'
            )
        return self._tokenizer

    @property
    def ai_detector_model(self):
        """Инициализирует и возвращает модель для детекции AI-текста."""
        if self._ai_detector_model is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
            self._ai_detector_model = AutoModelForSequenceClassification.from_pretrained(
                "roberta-base-openai-detector"
            ).to(device)
        return self._ai_detector_model

    @property
    def ai_detector_tokenizer(self):
        """Инициализирует и возвращает токенизатор для модели детекции AI-текста."""
        if self._ai_detector_tokenizer is None:
            self._ai_detector_tokenizer = AutoTokenizer.from_pretrained(
                "roberta-base-openai-detector"
            )
        return self._ai_detector_tokenizer

    @property
    def chatgpt4_detector_model(self):
        """Инициализирует и возвращает модель для детекции текста ChatGPT-4."""
        if self._chatgpt4_detector_model is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
            # Используем специализированную модель для определения ChatGPT-4
            # Обратите внимание, что нужно будет заменить путь на актуальную модель
            self._chatgpt4_detector_model = AutoModelForSequenceClassification.from_pretrained(
                "chatgpt4-detector-model-path"  # Заменить на реальный путь к модели
            ).to(device)
        return self._chatgpt4_detector_model

    @property
    def chatgpt4_detector_tokenizer(self):
        """Инициализирует и возвращает токенизатор для модели детекциии ChatGPT-4."""
        if self._chatgpt4_detector_tokenizer is None:
            self._chatgpt4_detector_tokenizer = AutoTokenizer.from_pretrained(
                "chatgpt4-detector-model-path"  # Заменить на реальный путь к модели
            )
        return self._chatgpt4_detector_tokenizer

    @property
    def deepseek_detector_model(self):
        """Инициализирует и возвращает модель для детекции текста DeepSeek."""
        if self._deepseek_detector_model is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
            # Используем специализированную модель для определения DeepSeek
            # Обратите внимание, что нужно будет заменить путь на актуальную модель
            self._deepseek_detector_model = AutoModelForSequenceClassification.from_pretrained(
                "deepseek-detector-model-path"  # Заменить на реальный путь к модели
            ).to(device)
        return self._deepseek_detector_model

    @property
    def deepseek_detector_tokenizer(self):
        """Инициализирует и возвращает токенизатор для модели детекции DeepSeek."""
        if self._deepseek_detector_tokenizer is None:
            self._deepseek_detector_tokenizer = AutoTokenizer.from_pretrained(
                "deepseek-detector-model-path"  # Заменить на реальный путь к модели
            )
        return self._deepseek_detector_tokenizer


model_loader = ModelLoader()