import spacy
import torch
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from typing import Optional
import logging
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)


class ModelLoader:
    """Класс для ленивой загрузки NLP моделей"""
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
            cls._instance._device = cls._instance._get_optimal_device()
            cls._instance.logger.info(f"Используемое устройство: {cls._instance._device}")
        return cls._instance

    def _get_optimal_device(self) -> str:
        """Определяет оптимальное устройство для вычислений"""
        if torch.cuda.is_available():
            try:
                test_tensor = torch.tensor([1.0]).cuda()
                _ = test_tensor * 2
                device = f"cuda:{torch.cuda.current_device()}"
                gpu_name = torch.cuda.get_device_name(0)
                memory = torch.cuda.get_device_properties(0).total_memory / 1024 ** 3
                self.logger.info(f"NVIDIA GPU найдена: {gpu_name}, Память: {memory:.1f}GB")
                return device
            except Exception as e:
                self.logger.warning(f"CUDA недоступна: {e}")

        try:
            import os
            if os.environ.get('ROCM_PATH') or os.environ.get('HIP_PATH'):
                test_tensor = torch.tensor([1.0], device='cuda:0')
                _ = test_tensor * 2
                self.logger.info("AMD GPU с ROCm найдена")
                return "cuda:0"
        except Exception:
            pass

        self.logger.info("Используется CPU")
        return "cpu"

    @property
    def device(self) -> str:
        return self._device

    @property
    def nlp(self) -> Optional[spacy.Language]:
        if self._nlp is None:
            try:
                self._nlp = spacy.load("ru_core_news_lg")
                self.logger.info("SpaCy модель загружена успешно")
            except Exception as e:
                self.logger.error(f"Ошибка загрузки spaCy модели: {e}")
                return None
        return self._nlp

    @property
    def model(self) -> Optional[SentenceTransformer]:
        if self._model is None:
            try:
                self.logger.info("Загрузка SentenceTransformer модели...")
                self._model = SentenceTransformer('paraphrase-xlm-r-multilingual-v1')
                self._model = self._model.to(self._device)

                if self._device.startswith('cuda'):
                    try:
                        self._model.half()
                    except:
                        pass

                model_device = next(self._model.parameters()).device
                self.logger.info(f"SentenceTransformer загружен на: {model_device}")

            except Exception as e:
                self.logger.error(f"Ошибка загрузки SentenceTransformer: {e}")
                return None
        return self._model

    @property
    def tokenizer(self) -> Optional[AutoTokenizer]:
        if self._tokenizer is None:
            try:
                self._tokenizer = AutoTokenizer.from_pretrained(
                    'sentence-transformers/paraphrase-xlm-r-multilingual-v1'
                )
                self.logger.info("Токенизатор загружен успешно")
            except Exception as e:
                self.logger.error(f"Ошибка загрузки токенизатора: {e}")
                return None
        return self._tokenizer

    def _load_classification_model(self, model_key: str, model_name: str):
        """Загрузка классификационной модели"""
        if model_key not in self._models:
            try:
                self.logger.info(f"Загрузка модели {model_name}...")

                # Пробуем несколько моделей для детекции AI
                model_variants = [
                    model_name,
                    'Hello-SimpleAI/chatgpt-detector-roberta',
                    'roberta-base-openai-detector',
                    'openai-detector'
                ]

                model = None
                for variant in model_variants:
                    try:
                        dtype = torch.float16 if self._device.startswith('cuda') else torch.float32
                        model = AutoModelForSequenceClassification.from_pretrained(
                            variant,
                            torch_dtype=dtype,
                            ignore_mismatched_sizes=True  # Игнорируем несоответствия размеров
                        )
                        model = model.to(self._device)
                        model.eval()
                        self.logger.info(f"Модель {variant} загружена на {self._device}")
                        break
                    except Exception as e:
                        self.logger.warning(f"Не удалось загрузить {variant}: {e}")
                        continue

                if model is None:
                    self.logger.warning("Не удалось загрузить ни одну модель детекции AI")
                    return None

                self._models[model_key] = model

            except Exception as e:
                self.logger.error(f"Критическая ошибка загрузки: {e}")
                return None

        return self._models.get(model_key)

    def _load_tokenizer(self, tokenizer_key: str, model_name: str):
        """Загрузка токенизатора"""
        if tokenizer_key not in self._tokenizers:
            try:
                # Пробуем несколько вариантов токенизаторов
                tokenizer_variants = [
                    model_name,
                    'Hello-SimpleAI/chatgpt-detector-roberta',
                    'roberta-base'
                ]

                tokenizer = None
                for variant in tokenizer_variants:
                    try:
                        tokenizer = AutoTokenizer.from_pretrained(variant)
                        self.logger.info(f"Токенизатор {variant} загружен успешно")
                        break
                    except Exception:
                        continue

                if tokenizer is None:
                    self.logger.warning("Не удалось загрузить токенизатор")
                    return None

                self._tokenizers[tokenizer_key] = tokenizer
            except Exception as e:
                self.logger.error(f"Ошибка загрузки токенизатора: {e}")
                return None
        return self._tokenizers.get(tokenizer_key)

    @property
    def ai_detector_model(self):
        """Основная модель для детекции AI-текста"""
        return self._load_classification_model('ai_detector', 'Hello-SimpleAI/chatgpt-detector-roberta')

    @property
    def ai_detector_tokenizer(self):
        """Токенизатор для основной модели"""
        return self._load_tokenizer('ai_detector', 'Hello-SimpleAI/chatgpt-detector-roberta')

    # Алиасы для совместимости
    @property
    def multilingual_detector_model(self):
        return self.ai_detector_model

    @property
    def multilingual_detector_tokenizer(self):
        return self.ai_detector_tokenizer

    @property
    def modern_ai_detector_model(self):
        return self.ai_detector_model

    @property
    def modern_ai_detector_tokenizer(self):
        return self.ai_detector_tokenizer

    def clear_cache(self):
        """Очищает кэш GPU"""
        if self._device.startswith('cuda'):
            torch.cuda.empty_cache()

    def get_memory_info(self) -> dict:
        """Информация о памяти устройства"""
        info = {"device": self._device}

        if self._device.startswith('cuda'):
            try:
                info.update({
                    "gpu_name": torch.cuda.get_device_name(0),
                    "allocated": f"{torch.cuda.memory_allocated() / 1024 ** 3:.2f}GB",
                    "cached": f"{torch.cuda.memory_reserved() / 1024 ** 3:.2f}GB",
                    "total": f"{torch.cuda.get_device_properties(0).total_memory / 1024 ** 3:.1f}GB"
                })
            except Exception as e:
                info["error"] = str(e)
        else:
            info["type"] = "CPU"

        return info


# Глобальный экземпляр
model_loader = ModelLoader()