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
     * Выделяет неуникальные предложения в тексте с улучшенным алгоритмом
     * @static
     * @param {string} fullText - Полный текст для анализа
     * @param {string[]} matchedSentences - Массив неуникальных предложений
     * @returns {string} - Текст с HTML-разметкой для выделения неуникальных фрагментов
     */
    static highlightNonUniqueText(fullText, matchedSentences) {
        if (!fullText || !matchedSentences || matchedSentences.length === 0) {
            return fullText; // Возвращаем уже экранированный текст
        }

        // Текст уже должен быть экранирован на этом этапе
        let processedText = fullText;

        // Создаем структуру для отслеживания позиций в тексте
        const positions = [];

        // Обрабатываем все неуникальные предложения
        matchedSentences.forEach(sentence => {
            // Игнорируем пустые или слишком короткие предложения
            if (!sentence || sentence.length < 3) return;

            const escapedSentence = this.escapeHtml(sentence);
            let startPos = 0;

            // Находим все вхождения предложения в тексте
            while (true) {
                const pos = processedText.indexOf(escapedSentence, startPos);
                if (pos === -1) break;

                positions.push({
                    start: pos,
                    end: pos + escapedSentence.length,
                    text: escapedSentence
                });

                startPos = pos + 1; // Ищем следующее вхождение
            }
        });

        // Сортируем позиции от конца к началу текста для правильной вставки HTML-тегов
        positions.sort((a, b) => b.start - a.start);

        // Устраняем перекрытия
        const nonOverlappingPositions = [];
        for (let i = 0; i < positions.length; i++) {
            let overlaps = false;

            for (let j = 0; j < nonOverlappingPositions.length; j++) {
                // Проверяем на перекрытие
                if (positions[i].start < nonOverlappingPositions[j].end &&
                    positions[i].end > nonOverlappingPositions[j].start) {
                    overlaps = true;
                    break;
                }
            }

            if (!overlaps) {
                nonOverlappingPositions.push(positions[i]);
            }
        }

        // Вставляем HTML-теги для выделения
        nonOverlappingPositions.forEach(pos => {
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