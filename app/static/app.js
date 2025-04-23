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

        // Инициализация компонентов
        this.fileHandler = new FileHandler(this.contentDiv, this.statusDiv);
        this.uiUpdater = new UIUpdater(
            this.resultsDiv,
            this.uniResultsDiv,
            this.seoResultsDiv,
            this.contentDiv
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
                    await this.fileHandler.handleFileUpload(file);
                    this.startButton.disabled = false;
                } catch (error) {
                    console.error('File processing error:', error);
                }
            }
        });

        // Обработчик ввода текста
        this.contentDiv.addEventListener('input', () => {
            this.startButton.disabled = false;
        });

        // Обработчик кнопки проверки
        this.startButton.addEventListener('click', () => {
            const text = this.contentDiv.textContent;
            const file = this.fileInput.files[0];
            this.apiService.checkForPlagiarism(text, file);
        });

        // Обработчик кнопки отмены
        this.cancelButton.addEventListener('click', () => {
            this.apiService.cancelRequest();
        });
    }
}

// Инициализация приложения после загрузки DOM
document.addEventListener('DOMContentLoaded', () => {
    new AntiPlagiarismApp();
});