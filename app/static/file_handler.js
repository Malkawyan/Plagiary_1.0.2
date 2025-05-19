import { MESSAGES } from './constants.js';

/**
 * Класс для обработки операций с файлами
 * Обеспечивает чтение и обработку различных форматов файлов
 */
export class FileHandler {
    /**
     * @constructor
     * @param {HTMLElement} contentDiv - Элемент для отображения содержимого файла
     * @param {HTMLElement} statusDiv - Элемент для отображения статуса операций
     */
    constructor(contentDiv, statusDiv) {
        this.contentDiv = contentDiv;
        this.statusDiv = statusDiv;
        this.originalText = '';  // Хранит оригинальный текст для последующей обработки
    }

    /**
     * Обрабатывает загруженный файл и извлекает текст
     * @param {File} file - Объект файла для обработки
     * @returns {Promise<string>} - Promise с извлеченным текстом
     */
    async handleFileUpload(file) {
        if (!file) return null;

        this.statusDiv.textContent = `${MESSAGES.FILE_SELECTED} ${file.name}`;

        try {
            // Обработка DOCX файлов с помощью библиотеки Mammoth
            if (file.name.endsWith('.docx')) {
                // Используем глобальный объект mammoth, загруженный через тег script
                const result = await window.mammoth.extractRawText({
                    arrayBuffer: await this.readFileAsArrayBuffer(file)
                });
                this.originalText = result.value;
            }
            // Обработка текстовых файлов
            else {
                this.originalText = await this.readFileAsText(file);
            }

            // Безопасно отображаем содержимое, экранируя HTML
            this.contentDiv.textContent = this.originalText;

            // Сохраняем оригинальный текст в data-атрибуте для безопасного доступа
            this.contentDiv.dataset.originalText = this.originalText;

            return this.originalText;
        } catch (error) {
            this.statusDiv.textContent = `${MESSAGES.FILE_PROCESSING_ERROR} ${error}`;
            throw error;
        }
    }

    /**
     * Читает файл как ArrayBuffer
     * @private
     * @param {File} file - Файл для чтения
     * @returns {Promise<ArrayBuffer>}
     */
    readFileAsArrayBuffer(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => resolve(e.target.result);
            reader.onerror = (error) => reject(error);
            reader.readAsArrayBuffer(file);
        });
    }

    /**
     * Читает файл как текст с учетом кодировки UTF-8
     * @private
     * @param {File} file - Файл для чтения
     * @returns {Promise<string>}
     */
    readFileAsText(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => {
                const decoder = new TextDecoder('utf-8');
                resolve(decoder.decode(e.target.result));
            };
            reader.onerror = (error) => reject(error);
            reader.readAsArrayBuffer(file);
        });
    }
}