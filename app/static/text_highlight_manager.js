import { TextProcessor } from './text_processor.js';

/**
 * Класс для управления подсветкой текста
 * Отвечает за выделение неуникальных фрагментов и орфографических ошибок
 */
export class TextHighlightManager {
    /**
     * Конвертирует HTML-текст в простой текст, сохраняя структуру для маппинга
     * @param {string} html - HTML-текст для преобразования
     * @returns {string} - Преобразованный текст
     */
    static convertHtmlToPlainText(html) {
        const tempElement = document.createElement('div');
        tempElement.innerHTML = html;
        return tempElement.textContent;
    }

    /**
     * Безопасно преобразует текст для вставки в HTML
     * @param {string} text - Текст для преобразования
     * @returns {string} - Безопасный HTML
     */
    static safeTextContent(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Применяет подсветку текста в соответствии с режимом просмотра
     * @param {string} originalText - Исходный текст
     * @param {Object} data - Данные проверки
     * @param {string} viewType - Тип просмотра ('all', 'uniqueness', 'spelling', 'ai', 'seo')
     * @returns {string} - Текст с HTML-подсветкой
     */
    static applyHighlighting(originalText, data, viewType) {
        if (!originalText) return '';
        if (!data) return TextProcessor.escapeHtml(originalText);

        // Экранируем HTML в оригинальном тексте
        let safeOriginalText = TextProcessor.escapeHtml(originalText);
        let processedText = safeOriginalText;

        // Подсвечиваем неуникальные фрагменты
        if ((viewType === 'uniqueness' || viewType === 'all') &&
            data.matched_sentences &&
            data.matched_sentences.length > 0) {
            processedText = TextProcessor.highlightNonUniqueText(
                safeOriginalText, data.matched_sentences
            );
        }

        // Подсвечиваем орфографические ошибки
        if ((viewType === 'spelling' || viewType === 'all') &&
            data.spelling_errors &&
            data.spelling_errors.length > 0) {

            // В зависимости от режима отображения
            if (viewType === 'spelling') {
                processedText = this.highlightSpellingErrors(
                    safeOriginalText,
                    data.spelling_errors
                );
            } else if (viewType === 'all') {
                // Для комбинированного режима
                processedText = this.highlightSpellingErrors(
                    safeOriginalText,
                    data.spelling_errors
                );
            }
        }

        return processedText;
    }

    /**
     * Выделяет орфографические ошибки в тексте
     * @param {string} text - Исходный текст
     * @param {Array} errors - Массив орфографических ошибок
     * @returns {string} - Текст с HTML-выделением ошибок
     */
    static highlightSpellingErrors(text, errors) {
        if (!errors || errors.length === 0 || !text) return this.safeTextContent(text);

        // Создаем массив для маркеров выделения
        const markers = [];

        // Обрабатываем каждую ошибку и ищем её точное положение в тексте
        for (const error of errors) {
            if (!error || !error.word || error.word.trim().length <= 1) {
                continue;
            }

            const errorWord = error.word.trim();

            // Ищем все вхождения ошибочного слова в тексте
            let searchText = text.toLowerCase();
            let searchWord = errorWord.toLowerCase();
            let pos = 0;

            while ((pos = searchText.indexOf(searchWord, pos)) !== -1) {
                // Проверяем, что найденное слово - отдельное слово, а не часть другого слова
                const prevChar = pos > 0 ? searchText.charAt(pos - 1) : ' ';
                const nextChar = pos + searchWord.length < searchText.length ?
                                 searchText.charAt(pos + searchWord.length) : ' ';

                const isBoundaryBefore = /[\s.,;:!?'"()\[\]{}<>—–-]/.test(prevChar);
                const isBoundaryAfter = /[\s.,;:!?'"()\[\]{}<>—–-]/.test(nextChar);

                if (isBoundaryBefore && isBoundaryAfter) {
                    // Получаем оригинальное слово из исходного текста (с сохранением регистра)
                    const originalWord = text.substring(pos, pos + errorWord.length);

                    // Добавляем маркер для выделения
                    markers.push({
                        start: pos,
                        end: pos + originalWord.length,
                        word: originalWord,
                        replacements: error.replacements || []
                    });
                }

                pos += searchWord.length;
            }
        }

        // Сортируем маркеры от конца к началу текста
        markers.sort((a, b) => b.start - a.start);

        // Строим результирующий HTML с выделенными ошибками
        let result = text;

        markers.forEach(marker => {
            const replacements = marker.replacements && marker.replacements.length > 0
                ? marker.replacements.slice(0, 3).join(', ')
                : 'нет вариантов';

            const before = result.substring(0, marker.start);
            const errorText = result.substring(marker.start, marker.end);
            const after = result.substring(marker.end);

            result = before +
                     `<span class="spelling-error" title="Варианты: ${replacements}">` +
                     errorText +
                     '</span>' +
                     after;
        });

        return result;
    }

    /**
     * Добавляет или обновляет стили для выделения текста
     */
    static ensureHighlightingStyles() {
        let styleElement = document.getElementById('highlight-styles');

        if (!styleElement) {
            styleElement = document.createElement('style');
            styleElement.id = 'highlight-styles';
            document.head.appendChild(styleElement);
        }

        styleElement.textContent = `
            .non-unique {
                background-color: #FFEB3B;
                display: inline;
                padding: 1px 0;
            }
            .spelling-error {
                color: red;
                text-decoration: underline wavy red;
            }
            .info-column {
                cursor: pointer;
                transition: background-color 0.3s ease;
            }
            .info-column:hover {
                background-color: #f0f0f0;
            }
            .info-column.active {
                background-color: #e0e0e0;
                border-left: 3px solid #4285f4;
            }
        `;
    }
}