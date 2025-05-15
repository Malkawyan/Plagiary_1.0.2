import spacy
import torch
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from typing import Optional
import logging


class ModelLoader:
    """
    Класс для ленивой загрузки и хранения NLP моделей с обработкой ошибок
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
            cls._instance.logger = logging.getLogger(__name__)
        return cls._instance

    @property
    def nlp(self) -> Optional[spacy.Language]:
        """Инициализирует и возвращает модель spaCy для русского языка."""
        if self._nlp is None:
            try:
                self._nlp = spacy.load("ru_core_news_lg")
            except Exception as e:
                self.logger.error(f"Ошибка загрузки spaCy модели: {e}")
                return None
        return self._nlp

    @property
    def model(self) -> Optional[SentenceTransformer]:
        """Инициализирует и возвращает модель SentenceTransformer."""
        if self._model is None:
            try:
                device = "cuda" if torch.cuda.is_available() else "cpu"
                self._model = SentenceTransformer(
                    'paraphrase-xlm-r-multilingual-v1'
                ).to(device)
            except Exception as e:
                self.logger.error(f"Ошибка загрузки SentenceTransformer: {e}")
                return None
        return self._model

    @property
    def tokenizer(self) -> Optional[AutoTokenizer]:
        """Инициализирует и возвращает токенизатор для модели."""
        if self._tokenizer is None:
            try:
                self._tokenizer = AutoTokenizer.from_pretrained(
                    'sentence-transformers/paraphrase-xlm-r-multilingual-v1'
                )
            except Exception as e:
                self.logger.error(f"Ошибка загрузки токенизатора: {e}")
                return None
        return self._tokenizer

    @property
    def ai_detector_model(self):
        """Модель для детекции AI-текста"""
        if 'ai_detector' not in self._models:
            try:
                device = "cuda" if torch.cuda.is_available() else "cpu"
                model_name = "roberta-base-openai-detector"
                self._models['ai_detector'] = AutoModelForSequenceClassification.from_pretrained(
                    model_name
                ).to(device)
            except Exception as e:
                self.logger.error(f"Ошибка загрузки модели детектора AI: {e}")
                return None
        return self._models.get('ai_detector')

    @property
    def ai_detector_tokenizer(self):
        """Токенизатор для модели детекции"""
        if 'ai_detector' not in self._tokenizers:
            try:
                model_name = "roberta-base-openai-detector"
                self._tokenizers['ai_detector'] = AutoTokenizer.from_pretrained(model_name)
            except Exception as e:
                self.logger.error(f"Ошибка загрузки токенизатора детектора AI: {e}")
                return None
        return self._tokenizers.get('ai_detector')

    @property
    def multilingual_detector_model(self):
        """Мультиязычная модель для детекции"""
        if 'multilingual_detector' not in self._models:
            try:
                device = "cuda" if torch.cuda.is_available() else "cpu"
                model_name = "Hello-SimpleAI/chatgpt-detector-roberta"
                self._models['multilingual_detector'] = AutoModelForSequenceClassification.from_pretrained(
                    model_name,
                    num_labels=2
                ).to(device)
            except Exception as e:
                self.logger.error(f"Ошибка загрузки мультиязычной модели: {e}")
                return None
        return self._models.get('multilingual_detector')

    @property
    def multilingual_detector_tokenizer(self):
        """Токенизатор для мультиязычной модели"""
        if 'multilingual_detector' not in self._tokenizers:
            try:
                model_name = "Hello-SimpleAI/chatgpt-detector-roberta"
                self._tokenizers['multilingual_detector'] = AutoTokenizer.from_pretrained(model_name)
            except Exception as e:
                self.logger.error(f"Ошибка загрузки мультиязычного токенизатора: {e}")
                return None
        return self._tokenizers.get('multilingual_detector')

    @property
    def modern_ai_detector_model(self):
        """Специальная модель для детекции современных ИИ"""
        if 'modern_ai_detector' not in self._models:
            try:
                device = "cuda" if torch.cuda.is_available() else "cpu"
                model_name = "Hello-SimpleAI/chatgpt-detector-roberta"
                self._models['modern_ai_detector'] = AutoModelForSequenceClassification.from_pretrained(
                    model_name,
                    num_labels=2
                ).to(device)
            except Exception as e:
                self.logger.error(f"Ошибка загрузки modern_ai_detector: {e}")
                return None
        return self._models.get('modern_ai_detector')

    @property
    def modern_ai_detector_tokenizer(self):
        """Токенизатор для модели детекции современных ИИ"""
        if 'modern_ai_detector' not in self._tokenizers:
            try:
                model_name = "Hello-SimpleAI/chatgpt-detector-roberta"
                self._tokenizers['modern_ai_detector'] = AutoTokenizer.from_pretrained(model_name)
            except Exception as e:
                self.logger.error(f"Ошибка загрузки токенизатора modern_ai_detector: {e}")
                return None
        return self._tokenizers.get('modern_ai_detector')


model_loader = ModelLoader()