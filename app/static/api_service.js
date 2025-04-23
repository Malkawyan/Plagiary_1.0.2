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
        this.cancelRequested = false;
    }

    /**
     * Отправляет текст на проверку
     * @param {string} text - Текст для проверки
     * @param {File|null} file - Опциональный файл
     * @returns {Promise<void>}
     */
    async checkForPlagiarism(text, file = null) {
        this.cancelRequested = false;
        this.uiUpdater.updateLoadingState(true);

        const formData = new FormData();
        formData.append('text', text);
        if (file) formData.append('file', file);

        try {
            const response = await fetch('/', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

            const data = await response.json();
            if (!this.cancelRequested) {
                this.uiUpdater.displayResults(data);
            }
        } catch (error) {
            if (!this.cancelRequested) {
                this.uiUpdater.displayError(error);
            }
        } finally {
            this.uiUpdater.updateLoadingState(false);
        }
    }

    /**
     * Отменяет текущий запрос
     */
    cancelRequest() {
        this.cancelRequested = true;
    }
}