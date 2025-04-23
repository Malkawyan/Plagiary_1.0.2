import { MESSAGES } from './constants.js';
import { TextProcessor } from './text_processor.js';

/**
 * Класс для управления обновлением пользовательского интерфейса
 * Инкапсулирует логику отображения результатов проверки
 */
export class UIUpdater {
    /**
     * @constructor
     * @param {HTMLElement} resultsDiv - Контейнер для основных результатов
     * @param {HTMLElement} uniResultsDiv - Контейнер для показателей уникальности
     * @param {HTMLElement} seoResultsDiv - Контейнер для SEO-анализа
     * @param {HTMLElement} contentDiv - Редактируемое поле с текстом
     */
    constructor(resultsDiv, uniResultsDiv, seoResultsDiv, contentDiv) {
        this.resultsDiv = resultsDiv;
        this.uniResultsDiv = uniResultsDiv;
        this.seoResultsDiv = seoResultsDiv;
        this.contentDiv = contentDiv;
    }

    /**
     * Обновляет состояние индикатора загрузки
     * @param {boolean} isLoading - Флаг активности процесса загрузки
     */
    updateLoadingState(isLoading) {
        if (isLoading) {
            this.resultsDiv.innerHTML = MESSAGES.LOADING;
        } else {
            this.resultsDiv.innerHTML = MESSAGES.DEFAULT_RESULTS;
        }
    }

    /**
     * Отображает результаты проверки уникальности
     * @param {Object} data - Результаты от API
     * @param {number} data.overall_uniqueness - Общий процент уникальности
     * @param {string[]} data.matched_sentences - Найденные заимствования
     * @param {Object} data.file_similarity - Сходство с другими файлами
     * @param {number} data.spam_score - Показатель спамности
     * @param {number} data.water_score - Показатель водянистости
     */
    displayResults(data) {
        const uniqueness = parseFloat(data.overall_uniqueness);
        const color = TextProcessor.getUniquenessColor(uniqueness);

        // Обновление блока с уникальностью
        this.uniResultsDiv.innerHTML = `Уникальность: ${uniqueness}%`;
        this.uniResultsDiv.style.color = color;
        this.resultsDiv.style.color = color;

        // Подсветка неуникальных фрагментов в тексте
        if (data.matched_sentences && data.matched_sentences.length > 0) {
            this.contentDiv.innerHTML = TextProcessor.highlightNonUniqueText(
                this.contentDiv.textContent,
                data.matched_sentences
            );
        }

        // Формирование HTML с результатами
        let resultsHTML = `<p>Уникальность: ${uniqueness.toFixed(2)}%</p>`;

        // Добавление информации о файлах с заимствованиями
        if (data.file_similarity && Object.keys(data.file_similarity).length > 0) {
            resultsHTML += '<p>Файлы с заимствованиями:</p><ul>';
            for (const [file, similarity] of Object.entries(data.file_similarity)) {
                resultsHTML += `<li>${file}: ${similarity.toFixed(2)}%</li>`;
            }
            resultsHTML += '</ul>';
        } else {
            resultsHTML += `<p>${MESSAGES.NO_PLAGIARISM}</p>`;
        }

        this.resultsDiv.innerHTML = resultsHTML;

        // Обновление SEO-анализа
        this.seoResultsDiv.innerHTML = `
            <p>Спамность: ${data.spam_score}%</p>
            <p>Водянистость: ${data.water_score}%</p>
        `;
    }

    /**
     * Отображает сообщение об ошибке
     * @param {string|Error} error - Объект ошибки или сообщение
     */
    displayError(error) {
        const errorMessage = error instanceof Error ? error.message : String(error);
        this.resultsDiv.innerHTML = `Ошибка: ${errorMessage}`;
    }
}