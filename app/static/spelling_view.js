import { TextProcessor } from './text_processor.js';
import { SPELLING_MESSAGES } from './constants.js';

/**
 * Класс для отображения результатов проверки орфографии
 */
export class SpellingView {
    /**
     * @constructor
     * @param {HTMLElement} spellingResultsDiv - DOM элемент для отображения результатов проверки
     */
    constructor(spellingResultsDiv) {
        this.spellingResultsDiv = spellingResultsDiv;
    }

    /**
     * Отображает результаты проверки орфографии
     * @param {Array} errors - Массив орфографических ошибок
     */
    displayResults(errors) {
        if (!errors || errors.length === 0) {
            this.spellingResultsDiv.innerHTML = `<p style="font-family: 'Times New Roman', Times, serif; font-size: 11px;">${SPELLING_MESSAGES.NO_ERRORS}</p>`;
            return;
        }

        // Группируем уникальные ошибки, чтобы не показывать повторяющиеся слова
        const uniqueErrors = this.groupUniqueErrors(errors);

        let html = `<div style="font-family: 'Times New Roman', Times, serif; font-size: 11px;">`;
        html += `<p>Найдено орфографических ошибок: ${uniqueErrors.length}</p>`;

        if (uniqueErrors.length > 0) {
            html += '<div class="spelling-list">';
            uniqueErrors.forEach(error => {
                const errorWord = TextProcessor.escapeHtml(error.word);
                const replacements = error.replacements && error.replacements.length > 0
                    ? error.replacements.slice(0, 3).map(r => TextProcessor.escapeHtml(r)).join(', ')
                    : 'нет вариантов';

                html += `
                <div class="spelling-item">
                    <span class="spelling-word">${errorWord}</span>
                    <div>Варианты: ${replacements}</div>
                </div>`;
            });
            html += '</div>';
        }

        html += '</div>';
        this.spellingResultsDiv.innerHTML = html;
    }

    /**
     * Группирует уникальные ошибки по словам
     * @private
     * @param {Array} errors - Массив орфографических ошибок
     * @returns {Array} - Массив уникальных ошибок
     */
    groupUniqueErrors(errors) {
        if (!errors || errors.length === 0) return [];

        const uniqueErrorWords = {};

        errors.forEach(error => {
            if (!error || !error.word) return;

            const word = error.word.trim();
            // Пропускаем пустые слова и слишком короткие
            if (word.length <= 1) return;

            // Если это не дубликат, добавляем его в список
            if (!uniqueErrorWords[word]) {
                uniqueErrorWords[word] = error;
            }
        });

        return Object.values(uniqueErrorWords);
    }
}