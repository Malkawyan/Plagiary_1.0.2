import { MESSAGES } from './constants.js';
import { TextProcessor } from './text_processor.js';
import { SPELLING_MESSAGES } from './constants.js';

export class UIUpdater {
    constructor(resultsDiv, uniResultsDiv, seoResultsDiv, contentDiv, aiResultsDiv) {
        this.resultsDiv = resultsDiv;
        this.uniResultsDiv = uniResultsDiv;
        this.seoResultsDiv = seoResultsDiv;
        this.contentDiv = contentDiv;
        this.aiResultsDiv = aiResultsDiv;
        this.data = null;
        this.currentView = 'all';
    }

    updateLoadingState(isLoading) {
        const loadingElement = document.getElementById('loading');
        if (isLoading) {
            loadingElement.style.display = 'block';
            this.resultsDiv.innerHTML = MESSAGES.LOADING;
        } else {
            loadingElement.style.display = 'none';
        }
    }

    displaySpellingResults(errors) {
        const spellingColumn = document.getElementById('spell-results');

        if (!errors || errors.length === 0) {
            spellingColumn.innerHTML = `<p style="font-family: 'Times New Roman', Times, serif; font-size: 11px;">${SPELLING_MESSAGES.NO_ERRORS}</p>`;
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
        spellingColumn.innerHTML = html;
    }

    // Группирует уникальные ошибки по словам
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

    // Преобразует HTML-текст в простой текст, сохраняя оригинальную структуру для маппинга
    convertHtmlToPlainText(html) {
        const tempElement = document.createElement('div');
        tempElement.innerHTML = html;

        // Заменяем все HTML-элементы их текстовым содержимым
        const plainText = tempElement.textContent;

        return plainText;
    }

    // Безопасно преобразует текст для вставки в HTML
    static safeTextContent(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Улучшенный метод выделения орфографических ошибок
    highlightSpellingErrors(text, errors) {
        if (!errors || errors.length === 0 || !text) return this.constructor.safeTextContent(text);

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

    // Собирает все текстовые узлы в контейнере
    collectTextNodes(container) {
        const textNodes = [];
        const treeWalker = document.createTreeWalker(
            container,
            NodeFilter.SHOW_TEXT,
            null,
            false
        );

        let node;
        while (node = treeWalker.nextNode()) {
            textNodes.push(node);
        }

        return textNodes;
    }

    switchView(viewType) {
        console.log(`Переключение режима отображения на: ${viewType}`);
        this.currentView = viewType;

        // Подсветим активную вкладку
        this.highlightActiveTab(viewType);

        // Всегда вызываем обновление отображения при переключении представления
        this.updateTextDisplay();
    }

    // Добавляем метод для подсветки активной вкладки
    highlightActiveTab(viewType) {
        // Находим все колонки и удаляем активный класс
        const columns = document.querySelectorAll('.info-column');
        columns.forEach(column => {
            column.classList.remove('active');
        });

        // Добавляем активный класс к выбранной колонке
        const activeColumn = document.querySelector(`.info-column[data-view="${viewType}"]`);
        if (activeColumn) {
            activeColumn.classList.add('active');
        }
    }

    updateTextDisplay() {
        // Получаем оригинальный текст
        const originalText = this.contentDiv.dataset.originalText || this.contentDiv.textContent;

        // Принудительно экранируем HTML в оригинальном тексте
        let safeOriginalText = TextProcessor.escapeHtml(originalText);
        let processedText = safeOriginalText;

        // Журналируем для отладки
        console.log(`Режим отображения: ${this.currentView}`);

        // Убедимся, что свойства CSS для выделений есть в документе
        this.ensureHighlightingStyles();

        // Если данных еще нет или режим "обычный текст", просто отображаем экранированный текст
        if (!this.data) {
            console.log("Данных проверки нет, отображаем оригинальный текст");
            this.contentDiv.innerHTML = safeOriginalText;
            return;
        }

        console.log(`Неуникальные предложения:`, this.data?.matched_sentences?.length || 0);
        console.log(`Орфографические ошибки:`, this.data?.spelling_errors?.length || 0);

        // Проверяем, какой режим отображения выбран
        if (this.currentView === 'uniqueness' || this.currentView === 'all') {
            // Проверяем наличие неуникальных предложений
            if (this.data.matched_sentences && this.data.matched_sentences.length > 0) {
                console.log("Применяем выделение неуникальных фрагментов");
                // Применяем улучшенный метод выделения к безопасному тексту
                processedText = TextProcessor.highlightNonUniqueText(
                    safeOriginalText, this.data.matched_sentences
                );
            } else {
                console.log("Неуникальных предложений не найдено");
            }
        }

        // Обрабатываем орфографические ошибки, если нужно
        if (this.currentView === 'spelling' || this.currentView === 'all') {
            if (this.data.spelling_errors && this.data.spelling_errors.length > 0) {
                console.log("Применяем выделение орфографических ошибок");

                // В зависимости от режима отображения
                if (this.currentView === 'spelling') {
                    // Для режима только орфографии - работаем с экранированным текстом
                    processedText = this.highlightSpellingErrors(
                        safeOriginalText,
                        this.data.spelling_errors
                    );
                } else if (this.currentView === 'all') {
                    // Для комбинированного режима применяем выделение орфографии к уже обработанному тексту
                    const plainText = this.convertHtmlToPlainText(processedText);
                    processedText = this.highlightSpellingErrors(
                        safeOriginalText,
                        this.data.spelling_errors
                    );
                }
            } else {
                console.log("Орфографических ошибок не найдено");
            }
        }

        // Обновляем содержимое
        this.contentDiv.innerHTML = processedText;
    }

    // Добавляет или обновляет стили для выделения неуникальных фрагментов
    ensureHighlightingStyles() {
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

    displayResults(data) {
        console.log("Полученные данные:", data);
        this.data = data;

        // Убедимся, что matched_sentences существует
        if (!this.data.matched_sentences) {
            this.data.matched_sentences = [];
        }

        // Убедимся, что spelling_errors существует
        if (!this.data.spelling_errors) {
            this.data.spelling_errors = [];
        }

        const uniqueness = parseFloat(data.overall_uniqueness).toFixed(2);
        const color = TextProcessor.getUniquenessColor(uniqueness);
        this.uniResultsDiv.innerHTML = `Уникальность: ${uniqueness}%`;
        this.uniResultsDiv.style.color = color;

        let outputHTML = '<h3>Результаты проверки на заимствования</h3>';

        // Добавим вывод общего количества найденных неуникальных предложений
        outputHTML += `<p>Найдено неуникальных фрагментов: ${this.data.matched_sentences.length}</p>`;

        if (data.file_similarity && Object.keys(data.file_similarity).length > 0) {
            outputHTML += '<h4>Найдены совпадения в файлах:</h4><ul>';

            for (const [filename, similarity] of Object.entries(data.file_similarity)) {
                const roundedSimilarity = parseFloat(similarity).toFixed(2);
                outputHTML += `<li>${TextProcessor.escapeHtml(filename)}: ${roundedSimilarity}% совпадений</li>`;
            }

            outputHTML += '</ul>';
        } else {
            outputHTML += '<p>Прямые заимствования не обнаружены</p>';
        }

        this.resultsDiv.innerHTML = outputHTML;

        const spamScore = parseFloat(data.spam_score || 0).toFixed(2);
        const waterScore = parseFloat(data.water_score || 0).toFixed(2);
        this.seoResultsDiv.innerHTML = `
            <p>Спамность: ${spamScore}%</p>
            <p>Водянистость: ${waterScore}%</p>
        `;

        if (data.ai_text_detected !== undefined) {
            this.displayAIResults(data);
        } else {
            this.aiResultsDiv.innerHTML = `<p class="ai-error">Данные анализа ИИ недоступны</p>`;
        }

        if (data.spelling_errors) {
            this.displaySpellingResults(data.spelling_errors);
        } else {
            const spellingColumn = document.getElementById('spell-results');
            spellingColumn.innerHTML = `<p>${SPELLING_MESSAGES.NO_ERRORS}</p>`;
        }

        // Сохраняем оригинальный текст перед обновлением отображения
        // Если this.contentDiv.dataset.originalText еще не установлен, используем текущий текст
        if (!this.contentDiv.dataset.originalText) {
            this.contentDiv.dataset.originalText = this.contentDiv.textContent;
        }

        // После обновления данных обновляем отображение
        this.updateTextDisplay();
    }

    displayError(error) {
        const errorMessage = error instanceof Error ? error.message : String(error);
        this.resultsDiv.innerHTML = `Ошибка: ${TextProcessor.escapeHtml(errorMessage)}`;
    }

    displayAIResults(data) {
        if (data.ai_text_detected !== undefined || data.overall_ai_score !== undefined) {
            let aiPercent = data.overall_ai_score ||
                           (typeof data.ai_text_detected === 'string' ?
                            parseFloat(data.ai_text_detected.replace('%', '')) :
                            data.ai_text_detected);

            // Калибровка отображения для современных ИИ
            aiPercent = Math.min(100, parseFloat(aiPercent) * 1.15).toFixed(2);

            let featuresHtml = '';
            if (data.stylistic_features) {
                featuresHtml = `
                    <div class="stylistic-features">
                        <h4>Маркеры ИИ-генерации:</h4>
                        <p>Переходные слова: ${data.stylistic_features.transition_words_count}</p>
                        <p>Оценка "перфектности": ${data.stylistic_features.perfectness_score}/1.0</p>
                        ${data.stylistic_features.ai_style_markers ? `
                        <p>Повторяемость: ${data.stylistic_features.ai_style_markers.repetition_score.toFixed(2)}</p>
                        ` : ''}
                    </div>
                `;
            }

            let chunksHtml = '';
            if (data.chunks && data.chunks.length > 0) {
                chunksHtml = '<div class="ai-detection-chunks"><h4>Анализ по фрагментам:</h4>';
                data.chunks.forEach(chunk => {
                    chunksHtml += `
                        <div class="chunk-item">
                            <div>
                                <span class="chunk-score" style="color: ${this.getAiColor(chunk.ai_score)}">
                                    ${chunk.ai_score}%
                                </span>
                            </div>
                            <div class="chunk-text">${TextProcessor.escapeHtml(chunk.text).substring(0, 150)}${chunk.text.length > 150 ? '...' : ''}</div>
                        </div>
                    `;
                });
                chunksHtml += '</div>';
            }

            this.aiResultsDiv.innerHTML = `
                <div class="ai-detection-result">
                    <h4>Анализ ИИ-текста (обнаружено ChatGPT/DeepSeek/Claude)</h4>
                    <div class="ai-meter">
                        <div class="ai-meter-fill"
                             style="width: ${aiPercent}%;
                                    background: ${this.getAiColor(aiPercent)};">
                        </div>
                    </div>
                    <p class="ai-percentage">${aiPercent}% вероятность ИИ-генерации</p>
                    ${featuresHtml}
                    ${chunksHtml}
                    <div class="confidence-level">
                        <p>Уверенность модели: ${this.getConfidenceLevel(aiPercent)}</p>
                    </div>
                </div>
            `;
        }
    }

    getConfidenceLevel(percent) {
        percent = parseFloat(percent);
        if (percent < 20 || percent > 80) return "Высокая";
        if (percent < 30 || percent > 70) return "Средняя";
        return "Низкая";
    }

    getAiColor(percent) {
        percent = parseFloat(percent);
        if (percent < 30) return '#4CAF50';
        if (percent < 70) return '#FFC107';
        return '#f44336';
    }
}