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
            cls._instance._models = {}
            cls._instance._tokenizers = {}
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
        """Современная модель для детекции AI-текста с поддержкой новых моделей"""
        if 'ai_detector' not in self._models:
            device = "cuda" if torch.cuda.is_available() else "cpu"
            model_name = "roberta-base-openai-detector"
            self._models['ai_detector'] = AutoModelForSequenceClassification.from_pretrained(
                model_name
            ).to(device)
        return self._models['ai_detector']

    @property
    def ai_detector_tokenizer(self):
        """Токенизатор для современной модели детекции"""
        if 'ai_detector' not in self._tokenizers:
            model_name = "roberta-base-openai-detector"
            self._tokenizers['ai_detector'] = AutoTokenizer.from_pretrained(model_name)
        return self._tokenizers['ai_detector']

    @property
    def multilingual_detector_model(self):
        """Мультиязычная модель для детекции"""
        if 'multilingual_detector' not in self._models:
            device = "cuda" if torch.cuda.is_available() else "cpu"
            model_name = "Hello-SimpleAI/chatgpt-detector-roberta"
            self._models['multilingual_detector'] = AutoModelForSequenceClassification.from_pretrained(
                model_name,
                num_labels=2
            ).to(device)
        return self._models['multilingual_detector']

    @property
    def multilingual_detector_tokenizer(self):
        """Токенизатор для мультиязычной модели"""
        if 'multilingual_detector' not in self._tokenizers:
            model_name = "Hello-SimpleAI/chatgpt-detector-roberta"
            self._tokenizers['multilingual_detector'] = AutoTokenizer.from_pretrained(model_name)
        return self._tokenizers['multilingual_detector']

    @property
    def modern_ai_detector_model(self):
        """Специальная модель для детекции современных ИИ (ChatGPT-4, Claude, DeepSeek)"""
        if 'modern_ai_detector' not in self._models:
            device = "cuda" if torch.cuda.is_available() else "cpu"
            model_name = "microsoft/deberta-v3-base"
            self._models['modern_ai_detector'] = AutoModelForSequenceClassification.from_pretrained(
                model_name,
                num_labels=2
            ).to(device)
        return self._models['modern_ai_detector']

    @property
    def modern_ai_detector_tokenizer(self):
        """Токенизатор для модели детекции современных ИИ"""
        if 'modern_ai_detector' not in self._tokenizers:
            model_name = "microsoft/deberta-v3-base"
            self._tokenizers['modern_ai_detector'] = AutoTokenizer.from_pretrained(model_name)
        return self._tokenizers['modern_ai_detector']


model_loader = ModelLoader()