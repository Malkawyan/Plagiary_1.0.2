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
                // Добавляем обработку ошибок и таймаут
                const mammothPromise = window.mammoth.extractRawText({
                    arrayBuffer: await this.readFileAsArrayBuffer(file)
                });

                // Добавляем таймаут к операции Mammoth для предотвращения зависания
                const result = await Promise.race([
                    mammothPromise,
                    new Promise((_, reject) =>
                        setTimeout(() => reject(new Error('Превышено время ожидания при обработке DOCX')), 30000)
                    )
                ]);

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
            console.error('Ошибка обработки файла:', error);
            this.statusDiv.textContent = `${MESSAGES.FILE_PROCESSING_ERROR} ${error.message || error}`;
            // Возвращаем пустую строку вместо выбрасывания исключения
            return '';
        }
    }

    /**
     * Читает файл как ArrayBuffer с таймаутом
     * @private
     * @param {File} file - Файл для чтения
     * @returns {Promise<ArrayBuffer>}
     */
    readFileAsArrayBuffer(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();

            // Добавляем таймаут для FileReader
            const timeoutId = setTimeout(() => {
                reader.abort(); // Прерываем операцию чтения
                reject(new Error('Превышено время ожидания при чтении файла'));
            }, 15000); // 15 секунд таймаут

            reader.onload = (e) => {
                clearTimeout(timeoutId);
                resolve(e.target.result);
            };

            reader.onerror = (error) => {
                clearTimeout(timeoutId);
                reject(error || new Error('Ошибка чтения файла'));
            };

            reader.readAsArrayBuffer(file);
        });
    }

    /**
     * Читает файл как текст с учетом кодировки UTF-8 и таймаутом
     * @private
     * @param {File} file - Файл для чтения
     * @returns {Promise<string>}
     */
    readFileAsText(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();

            // Добавляем таймаут для FileReader
            const timeoutId = setTimeout(() => {
                reader.abort(); // Прерываем операцию чтения
                reject(new Error('Превышено время ожидания при чтении файла'));
            }, 15000); // 15 секунд таймаут

            reader.onload = (e) => {
                clearTimeout(timeoutId);
                try {
                    const decoder = new TextDecoder('utf-8');
                    resolve(decoder.decode(e.target.result));
                } catch (error) {
                    reject(error || new Error('Ошибка декодирования файла'));
                }
            };

            reader.onerror = (error) => {
                clearTimeout(timeoutId);
                reject(error || new Error('Ошибка чтения файла'));
            };

            reader.readAsArrayBuffer(file);
        });
    }
}