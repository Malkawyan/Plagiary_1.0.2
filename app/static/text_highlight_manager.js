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

        let processedText = originalText;

        // Подсвечиваем неуникальные фрагменты
        if ((viewType === 'uniqueness' || viewType === 'all') &&
            data.matched_sentences &&
            data.matched_sentences.length > 0) {
            // Экранируем HTML в оригинальном тексте
            let safeOriginalText = TextProcessor.escapeHtml(originalText);
            processedText = TextProcessor.highlightNonUniqueText(
                safeOriginalText, data.matched_sentences
            );
        }

        // Подсвечиваем орфографические ошибки
        if ((viewType === 'spelling' || viewType === 'all') &&
            data.spelling_errors &&
            data.spelling_errors.length > 0) {

            processedText = this.highlightSpellingErrors(
                processedText,
                data.spelling_errors,
                originalText
            );
        }

        // Если не было подсветки, экранируем HTML
        if (processedText === originalText) {
            processedText = TextProcessor.escapeHtml(originalText);
        }

        return processedText;
    }

    /**
     * Выделяет орфографические ошибки в тексте
     * @param {string} text - Текст для обработки (может быть уже с HTML-разметкой)
     * @param {Array} errors - Массив орфографических ошибок
     * @param {string} originalText - Оригинальный неэкранированный текст
     * @returns {string} - Текст с HTML-выделением ошибок
     */
    static highlightSpellingErrors(text, errors, originalText) {
        if (!errors || errors.length === 0 || !text) {
            return text === originalText ? this.safeTextContent(text) : text;
        }

        // Если текст не содержит HTML-разметки, работаем с оригинальным текстом
        const workingText = text === originalText ? originalText : text;
        const isHtmlText = text !== originalText;

        // Создаем массив уникальных слов-ошибок
        const uniqueErrors = new Set();
        for (const error of errors) {
            if (error && error.word && error.word.trim().length > 1) {
                uniqueErrors.add(error.word.trim().toLowerCase());
            }
        }

        if (uniqueErrors.size === 0) {
            return isHtmlText ? text : this.safeTextContent(text);
        }

        // Создаем карту ошибок с их заменами
        const errorMap = new Map();
        for (const error of errors) {
            if (error && error.word && error.word.trim().length > 1) {
                const word = error.word.trim().toLowerCase();
                if (!errorMap.has(word)) {
                    errorMap.set(word, error.replacements || []);
                }
            }
        }

        // Разбиваем текст на слова с сохранением разделителей
        const tokens = this.tokenizeText(isHtmlText ? this.stripHtmlTags(workingText) : workingText);
        let result = '';

        for (const token of tokens) {
            if (token.isWord) {
                const lowerWord = token.text.toLowerCase();
                if (uniqueErrors.has(lowerWord)) {
                    // Это ошибочное слово - выделяем его
                    const replacements = errorMap.get(lowerWord) || [];
                    const replacementText = replacements.length > 0
                        ? replacements.slice(0, 3).join(', ')
                        : 'нет вариантов';

                    result += `<span class="spelling-error" title="Варианты: ${this.safeTextContent(replacementText)}">${this.safeTextContent(token.text)}</span>`;
                } else {
                    // Обычное слово
                    result += this.safeTextContent(token.text);
                }
            } else {
                // Разделитель (пробелы, знаки препинания и т.д.)
                result += this.safeTextContent(token.text);
            }
        }

        return result;
    }

    /**
     * Разбивает текст на токены (слова и разделители)
     * @param {string} text - Текст для разбивки
     * @returns {Array} - Массив токенов
     */
    static tokenizeText(text) {
        const tokens = [];
        let currentToken = '';
        let isInWord = false;

        for (let i = 0; i < text.length; i++) {
            const char = text[i];
            const isWordChar = /[а-яёa-z0-9]/i.test(char);

            if (isWordChar) {
                if (!isInWord) {
                    // Начало нового слова - сохраняем предыдущий токен если есть
                    if (currentToken) {
                        tokens.push({ text: currentToken, isWord: false });
                    }
                    currentToken = char;
                    isInWord = true;
                } else {
                    // Продолжение слова
                    currentToken += char;
                }
            } else {
                if (isInWord) {
                    // Конец слова - сохраняем слово
                    if (currentToken) {
                        tokens.push({ text: currentToken, isWord: true });
                    }
                    currentToken = char;
                    isInWord = false;
                } else {
                    // Продолжение разделителя
                    currentToken += char;
                }
            }
        }

        // Сохраняем последний токен
        if (currentToken) {
            tokens.push({ text: currentToken, isWord: isInWord });
        }

        return tokens;
    }

    /**
     * Удаляет HTML-теги из текста
     * @param {string} html - HTML-текст
     * @returns {string} - Текст без HTML-тегов
     */
    static stripHtmlTags(html) {
        const tempElement = document.createElement('div');
        tempElement.innerHTML = html;
        return tempElement.textContent || tempElement.innerText || '';
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