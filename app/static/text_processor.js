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
        return text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    /**
     * Выделяет неуникальные предложения в тексте
     * @static
     * @param {string} fullText - Полный текст для анализа (уже экранированный)
     * @param {string[]} matchedSentences - Массив неуникальных предложений (неэкранированных)
     * @returns {string} - Текст с HTML-разметкой для выделения неуникальных фрагментов
     */
    static highlightNonUniqueText(fullText, matchedSentences) {
        if (!fullText || !matchedSentences || matchedSentences.length === 0) {
            return fullText;
        }

        let processedText = fullText;
        const positions = [];

        // Обрабатываем каждое неуникальное предложение
        matchedSentences.forEach(sentence => {
            if (!sentence || sentence.trim().length < 3) return;

            const trimmedSentence = sentence.trim();
            const escapedSentence = this.escapeHtml(trimmedSentence);

            // Ищем точные совпадения
            let startPos = 0;
            while (true) {
                const pos = processedText.indexOf(escapedSentence, startPos);
                if (pos === -1) break;

                // Проверяем границы слов для более точного совпадения
                const isValidMatch = this.isWordBoundary(processedText, pos, pos + escapedSentence.length);

                if (isValidMatch) {
                    positions.push({
                        start: pos,
                        end: pos + escapedSentence.length,
                        text: escapedSentence
                    });
                }

                startPos = pos + 1;
            }
        });

        // Удаляем перекрывающиеся позиции
        const cleanPositions = this.removeOverlaps(positions);

        // Сортируем от конца к началу для правильной вставки тегов
        cleanPositions.sort((a, b) => b.start - a.start);

        // Вставляем HTML-теги
        cleanPositions.forEach(pos => {
            processedText =
                processedText.substring(0, pos.start) +
                '<span class="non-unique" style="background-color: yellow; color: black;">' +
                pos.text +
                '</span>' +
                processedText.substring(pos.end);
        });

        return processedText;
    }

    /**
     * Проверяет, находится ли найденный текст на границах слов
     * @static
     * @param {string} text - Полный текст
     * @param {number} start - Начальная позиция
     * @param {number} end - Конечная позиция
     * @returns {boolean} - true, если это валидная граница слов
     */
    static isWordBoundary(text, start, end) {
        // Проверяем символы до и после найденного фрагмента
        const charBefore = start > 0 ? text[start - 1] : ' ';
        const charAfter = end < text.length ? text[end] : ' ';

        // Определяем, является ли символ разделителем
        const isDelimiter = (char) => /[\s\n\r\t.,;:!?()[\]{}"|«»„"'`]/.test(char);

        return isDelimiter(charBefore) && isDelimiter(charAfter);
    }

    /**
     * Удаляет перекрывающиеся позиции, оставляя более длинные
     * @static
     * @param {Array} positions - Массив позиций
     * @returns {Array} - Массив без перекрытий
     */
    static removeOverlaps(positions) {
        if (positions.length <= 1) return positions;

        // Сортируем по длине (от длинных к коротким)
        positions.sort((a, b) => (b.end - b.start) - (a.end - a.start));

        const result = [];

        for (const pos of positions) {
            let hasOverlap = false;

            for (const existing of result) {
                if (pos.start < existing.end && pos.end > existing.start) {
                    hasOverlap = true;
                    break;
                }
            }

            if (!hasOverlap) {
                result.push(pos);
            }
        }

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