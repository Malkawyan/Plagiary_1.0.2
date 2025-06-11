import { UIUpdater } from './ui_updater.js';

/**
 * Класс для взаимодействия с API антиплагиата
 * Инкапсулирует логику отправки запросов и обработки ответов
 */
export class ApiService {
    /**
     * @constructor
     * @param {UIUpdater} uiUpdater - Экземпляр класса для обновления UI
     */
    constructor(uiUpdater) {
        this.uiUpdater = uiUpdater;
        this.abortController = null; // Контроллер для отмены запросов
    }

    /**
     * Отправляет текст на проверку
     * @param {string} text - Текст для проверки
     * @param {File|null} file - Опциональный файл
     * @returns {Promise<void>}
     */
    async checkForPlagiarism(text, file = null) {
        // Отменяем предыдущий запрос, если он выполняется
        if (this.abortController) {
            this.abortController.abort();
        }

        // Создаем новый контроллер для текущего запроса
        this.abortController = new AbortController();

        this.uiUpdater.updateLoadingState(true);

        const formData = new FormData();
        formData.append('text', text);
        if (file) formData.append('file', file);

        try {
            const response = await fetch('/', {
                method: 'POST',
                body: formData,
                signal: this.abortController.signal // Передаем сигнал для отмены
            });

            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

            const data = await response.json();
            this.uiUpdater.displayResults(data);

        } catch (error) {
            // Проверяем, была ли операция отменена
            if (error.name === 'AbortError') {
                console.log('Запрос был отменен пользователем');
                this.uiUpdater.displayCancelMessage();
            } else {
                console.error('Ошибка при выполнении запроса:', error);
                this.uiUpdater.displayError(error);
            }
        } finally {
            this.uiUpdater.updateLoadingState(false);
            this.abortController = null; // Очищаем контроллер
        }
    }

    /**
     * Отменяет текущий запрос
     */
    cancelRequest() {
        if (this.abortController) {
            this.abortController.abort();
            console.log('Запрос отменен');
        }
    }
}