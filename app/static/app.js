import { FileHandler } from './file_handler.js';
import { ApiService } from './api_service.js';
import { UIUpdater } from './ui_updater.js';

/**
 * Класс инициализации и управления приложением
 * Связывает все компоненты системы
 */
export class AntiPlagiarismApp {
    constructor() {
        // Инициализация DOM-элементов
        this.startButton = document.getElementById('start-button');
        this.cancelButton = document.getElementById('cancel-button');
        this.statusDiv = document.getElementById('status');
        this.resultsDiv = document.getElementById('output');
        this.contentDiv = document.getElementById('file-content');
        this.fileInput = document.getElementById('file-input');
        this.uniResultsDiv = document.getElementById('uni-results');
        this.seoResultsDiv = document.getElementById('seo-results');
        this.aiResultsDiv = document.getElementById('ai-results');
        this.spellResultsDiv = document.getElementById('spell-results');

        if (!this.aiResultsDiv) console.error('Элемент #ai-results не найден!');

        // Получаем ссылки на все колонки с типами анализа
        this.infoColumns = document.querySelectorAll('.info-column');

        // Инициализация компонентов
        this.fileHandler = new FileHandler(this.contentDiv, this.statusDiv);
        this.uiUpdater = new UIUpdater(
            this.resultsDiv,
            this.uniResultsDiv,
            this.seoResultsDiv,
            this.contentDiv,
            this.aiResultsDiv
        );
        this.apiService = new ApiService(this.uiUpdater);

        // Настройка обработчиков событий
        this.setupEventListeners();
    }

    /**
     * Устанавливает обработчики событий для элементов интерфейса
     * @private
     */
    setupEventListeners() {
        // Обработчик загрузки файла
        this.fileInput.addEventListener('change', async (event) => {
            const file = event.target.files[0];
            if (file) {
                try {
                    // Очищаем содержимое перед загрузкой нового файла
                    this.contentDiv.innerHTML = '';

                    await this.fileHandler.handleFileUpload(file);
                    this.startButton.disabled = false;

                    // После загрузки файла сохраняем текст в data-атрибут для безопасного доступа
                    this.contentDiv.dataset.originalText = this.contentDiv.textContent;
                } catch (error) {
                    console.error('File processing error:', error);
                    this.statusDiv.textContent = 'Ошибка при обработке файла';
                }
            }
        });

        // Обработчик ввода текста
        this.contentDiv.addEventListener('input', () => {
            this.startButton.disabled = false;
            // Обновляем оригинальный текст при ручном редактировании
            this.contentDiv.dataset.originalText = this.contentDiv.textContent;
        });

        // Обработчик кнопки проверки
        this.startButton.addEventListener('click', () => {
            // Используем оригинальный текст из data-атрибута или текущий текст
            const text = this.contentDiv.dataset.originalText || this.contentDiv.textContent;
            const file = this.fileInput.files[0];
            this.apiService.checkForPlagiarism(text, file);
        });

        // Обработчик кнопки отмены
        this.cancelButton.addEventListener('click', () => {
            this.apiService.cancelRequest();
        });

        // Обработчики для колонок с типами анализа
        this.setupInfoColumnClickHandlers();
    }

    /**
     * Устанавливает обработчики нажатия на колонки с типами анализа
     */
    setupInfoColumnClickHandlers() {
        // Настраиваем обработчики для всех колонок
        this.infoColumns.forEach(column => {
            column.addEventListener('click', () => {
                // Получаем тип представления из атрибута data-view
                const viewType = column.getAttribute('data-view');
                if (viewType) {
                    this.uiUpdater.switchView(viewType);
                }
            });
        });
    }
}

// Инициализация приложения после загрузки DOM
document.addEventListener('DOMContentLoaded', () => {
    new AntiPlagiarismApp();
});