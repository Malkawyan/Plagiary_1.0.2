import { UNIQUENESS_COLORS, UNIQUENESS_THRESHOLDS } from './constants.js';

/**
 * Класс для обработки и анализа текста
 * Содержит методы для экранирования HTML и выделения неуникальных фрагментов
 */
export class TextProcessor {
    /**
     * Экранирует HTML-символы в тексте для безопасного отображения
     * @static
     * @param {string} text - Текст для экранирования
     * @returns {string} - Экранированный текст
     */
    static escapeHtml(text) {
        if (!text || typeof text !== 'string') return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Выделяет неуникальные предложения в тексте
     * @static
     * @param {string} fullText - Полный текст для анализа
     * @param {string[]} matchedSentences - Массив неуникальных предложений
     * @returns {string} - Текст с HTML-разметкой для выделения неуникальных фрагментов
     */
    static highlightNonUniqueText(fullText, matchedSentences) {
        // Проверка на пустые входные данные
        if (!fullText || !matchedSentences || matchedSentences.length === 0) {
            return this.escapeHtml(fullText);
        }

        const escapedText = this.escapeHtml(fullText);
        let result = escapedText;
        const matches = [];
        const textChars = new Array(escapedText.length).fill(false);

        // Сортировка предложений по длине для правильного вложения
        const sortedSentences = [...matchedSentences].sort((a, b) => b.length - a.length);

        // Поиск всех вхождений каждого предложения в тексте
        sortedSentences.forEach(sentence => {
            const escapedSentence = this.escapeHtml(sentence);
            let index = escapedText.indexOf(escapedSentence);

            // Обработка всех вхождений предложения в тексте
            while (index !== -1) {
                let canHighlight = true;

                // Проверка на пересечение с уже выделенными областями
                for (let i = index; i < index + escapedSentence.length; i++) {
                    if (textChars[i]) {
                        canHighlight = false;
                        break;
                    }
                }

                if (canHighlight) {
                    matches.push({
                        start: index,
                        end: index + escapedSentence.length,
                        text: escapedSentence
                    });

                    // Помечаем символы как выделенные
                    for (let i = index; i < index + escapedSentence.length; i++) {
                        textChars[i] = true;
                    }
                }

                // Поиск следующего вхождения
                index = escapedText.indexOf(escapedSentence, index + 1);
            }
        });

        // Вставка HTML-тегов для выделения, начиная с конца текста
        matches.sort((a, b) => b.start - a.start).forEach(match => {
            result = result.substring(0, match.start) +
                     '<span class="non-unique">' + match.text + '</span>' +
                     result.substring(match.end);
        });

        return result;
    }

    /**
     * Определяет цвет для отображения уровня уникальности
     * @static
     * @param {number} uniqueness - Процент уникальности (0-100)
     * @returns {string} - Цвет из UNIQUENESS_COLORS
     */
    static getUniquenessColor(uniqueness) {
        if (uniqueness >= UNIQUENESS_THRESHOLDS.HIGH) {
            return UNIQUENESS_COLORS.HIGH;
        } else if (uniqueness >= UNIQUENESS_THRESHOLDS.MEDIUM) {
            return UNIQUENESS_COLORS.MEDIUM;
        } else {
            return UNIQUENESS_COLORS.LOW;
        }
    }
}