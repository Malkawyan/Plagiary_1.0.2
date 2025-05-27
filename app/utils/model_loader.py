import spacy
import torch
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from typing import Optional
import logging
import warnings

# Подавляем предупреждения для чистого вывода
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)


class ModelLoader:
    """
    Класс для ленивой загрузки и хранения NLP моделей с поддержкой NVIDIA и AMD GPU
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
            cls._instance._device = cls._instance._get_optimal_device()
            cls._instance.logger.info(f"Используемое устройство: {cls._instance._device}")
        return cls._instance

    def _get_optimal_device(self) -> str:
        """Определяет оптимальное устройство для вычислений"""
        # Проверяем NVIDIA CUDA
        if torch.cuda.is_available():
            try:
                # Тестовая операция на GPU
                test_tensor = torch.tensor([1.0]).cuda()
                _ = test_tensor * 2
                device = f"cuda:{torch.cuda.current_device()}"
                gpu_name = torch.cuda.get_device_name(0)
                memory = torch.cuda.get_device_properties(0).total_memory / 1024 ** 3
                self.logger.info(f"NVIDIA GPU найдена: {gpu_name}, Память: {memory:.1f}GB")
                return device
            except Exception as e:
                self.logger.warning(f"CUDA недоступна: {e}")

        # Проверяем AMD ROCm (использует тот же CUDA API)
        try:
            # ROCm может быть доступен через переменные окружения
            import os
            if os.environ.get('ROCM_PATH') or os.environ.get('HIP_PATH'):
                # Пробуем создать тензор на "CUDA" устройстве (ROCm эмулирует CUDA API)
                test_tensor = torch.tensor([1.0], device='cuda:0')
                _ = test_tensor * 2
                self.logger.info("AMD GPU с ROCm найдена")
                return "cuda:0"
        except Exception:
            pass

        # Fallback на CPU
        self.logger.info("Используется CPU")
        return "cpu"

    @property
    def device(self) -> str:
        """Возвращает текущее устройство"""
        return self._device

    @property
    def nlp(self) -> Optional[spacy.Language]:
        """Инициализирует и возвращает модель spaCy для русского языка."""
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
        """Инициализирует и возвращает модель SentenceTransformer."""
        if self._model is None:
            try:
                self.logger.info("Загрузка SentenceTransformer модели...")
                self._model = SentenceTransformer('paraphrase-xlm-r-multilingual-v1')

                # Перемещаем на нужное устройство
                self._model = self._model.to(self._device)

                # Используем float16 для GPU для экономии памяти
                if self._device.startswith('cuda'):
                    try:
                        self._model.half()
                    except:
                        pass  # Если не поддерживается, используем float32

                model_device = next(self._model.parameters()).device
                self.logger.info(f"SentenceTransformer загружен на: {model_device}")

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
                self.logger.info("Токенизатор загружен успешно")
            except Exception as e:
                self.logger.error(f"Ошибка загрузки токенизатора: {e}")
                return None
        return self._tokenizer

    def _load_classification_model(self, model_key: str, model_name: str):
        """Универсальный метод для загрузки классификационных моделей"""
        if model_key not in self._models:
            try:
                self.logger.info(f"Загрузка модели {model_name}...")

                # Выбираем тип данных в зависимости от устройства
                dtype = torch.float16 if self._device.startswith('cuda') else torch.float32

                model = AutoModelForSequenceClassification.from_pretrained(
                    model_name,
                    torch_dtype=dtype
                )

                # Перемещаем на устройство
                model = model.to(self._device)
                model.eval()  # Режим инференса

                self._models[model_key] = model
                self.logger.info(f"Модель {model_name} загружена на {self._device}")

            except Exception as e:
                self.logger.error(f"Ошибка загрузки модели {model_name}: {e}")

                # Пробуем загрузить на CPU если не хватает GPU памяти
                if 'out of memory' in str(e).lower() and self._device.startswith('cuda'):
                    try:
                        self.logger.warning("Загружаем на CPU из-за нехватки GPU памяти...")
                        model = AutoModelForSequenceClassification.from_pretrained(model_name)
                        model = model.to('cpu')
                        model.eval()
                        self._models[model_key] = model
                        self.logger.info(f"Модель {model_name} загружена на CPU")
                    except Exception:
                        return None
                else:
                    return None

        return self._models.get(model_key)

    def _load_tokenizer(self, tokenizer_key: str, model_name: str):
        """Универсальный метод для загрузки токенизаторов"""
        if tokenizer_key not in self._tokenizers:
            try:
                tokenizer = AutoTokenizer.from_pretrained(model_name)
                self._tokenizers[tokenizer_key] = tokenizer
                self.logger.info(f"Токенизатор для {model_name} загружен успешно")
            except Exception as e:
                self.logger.error(f"Ошибка загрузки токенизатора для {model_name}: {e}")
                return None
        return self._tokenizers.get(tokenizer_key)

    @property
    def ai_detector_model(self):
        """Модель для детекции AI-текста"""
        return self._load_classification_model('ai_detector', 'roberta-base-openai-detector')

    @property
    def ai_detector_tokenizer(self):
        """Токенизатор для модели детекции"""
        return self._load_tokenizer('ai_detector', 'roberta-base-openai-detector')

    @property
    def multilingual_detector_model(self):
        """Мультиязычная модель для детекции"""
        return self._load_classification_model('multilingual_detector', 'Hello-SimpleAI/chatgpt-detector-roberta')

    @property
    def multilingual_detector_tokenizer(self):
        """Токенизатор для мультиязычной модели"""
        return self._load_tokenizer('multilingual_detector', 'Hello-SimpleAI/chatgpt-detector-roberta')

    @property
    def modern_ai_detector_model(self):
        """Специальная модель для детекции современных ИИ"""
        return self._load_classification_model('modern_ai_detector', 'Hello-SimpleAI/chatgpt-detector-roberta')

    @property
    def modern_ai_detector_tokenizer(self):
        """Токенизатор для модели детекции современных ИИ"""
        return self._load_tokenizer('modern_ai_detector', 'Hello-SimpleAI/chatgpt-detector-roberta')

    def clear_cache(self):
        """Очищает кэш GPU для освобождения памяти"""
        if self._device.startswith('cuda'):
            torch.cuda.empty_cache()
            self.logger.info("GPU кэш очищен")

    def get_memory_info(self) -> dict:
        """Возвращает информацию о памяти устройства"""
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


# Создаем глобальный экземпляр
model_loader = ModelLoader()