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
            const word = error.word;
            // Если слово является самостоятельным (не частью другого слова), добавляем его
            if (this.isStandaloneWord(error, this.contentDiv.textContent) && word.length > 1) {
                if (!uniqueErrorWords[word]) {
                    uniqueErrorWords[word] = error;
                }
            }
        });

        return Object.values(uniqueErrorWords);
    }

    // Проверяет, является ли слово самостоятельным (не частью другого слова)
    isStandaloneWord(error, text) {
        const offset = error.offset;
        const word = error.word;

        // Проверяем символы до и после слова
        const charBefore = offset > 0 ? text[offset - 1] : ' ';
        const charAfter = offset + word.length < text.length ? text[offset + word.length] : ' ';

        const isWordBoundaryBefore = !this.isWordChar(charBefore);
        const isWordBoundaryAfter = !this.isWordChar(charAfter);

        return isWordBoundaryBefore && isWordBoundaryAfter;
    }

    // Проверяет, является ли символ частью слова
    isWordChar(char) {
        return /[\p{L}\p{N}]/u.test(char); // Включает буквы и цифры всех языков
    }

    // Безопасно преобразует текст для вставки в HTML
    static safeTextContent(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Измененный метод для выделения орфографических ошибок в тексте
    highlightSpellingErrors(text, errors) {
        if (!errors || errors.length === 0 || !text) return this.constructor.safeTextContent(text);

        // Сначала экранируем текст для безопасного HTML
        let safeText = this.constructor.safeTextContent(text);
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = safeText;

        // Получаем чистый текст для сравнения с ошибками
        const plainText = tempDiv.textContent;

        // Создаем массив для отслеживания смещений
        const offsets = new Array(plainText.length);
        for (let i = 0; i < plainText.length; i++) {
            offsets[i] = i;
        }

        // Сортируем ошибки по смещению в обратном порядке
        const sortedErrors = [...errors]
            .filter(error => error && error.offset !== undefined && error.length > 0)
            .sort((a, b) => b.offset - a.offset);

        // Проходим по каждой ошибке, начиная с конца текста
        for (const error of sortedErrors) {
            const start = error.offset;
            const length = error.length || error.word?.length || 0;
            if (start < 0 || start >= plainText.length || length <= 0) continue;

            const end = Math.min(start + length, plainText.length);
            const errorWord = plainText.slice(start, end);

            if (!errorWord || errorWord.trim() === '') continue;

            // Создаем элемент с выделением
            const replacements = error.replacements && error.replacements.length > 0
                ? error.replacements.slice(0, 3).join(', ')
                : 'нет вариантов';

            safeText = safeText.substring(0, start) +
                      `<span class="spelling-error" title="Варианты: ${replacements}" style="color: red; text-decoration: underline wavy red;">` +
                      errorWord +
                      '</span>' +
                      safeText.substring(end);
        }

        return safeText;
    }

    switchView(viewType) {
        this.currentView = viewType;
        if (this.data) {
            this.updateTextDisplay();
        }
    }

    updateTextDisplay() {
        const originalText = this.contentDiv.dataset.originalText || this.contentDiv.textContent;
        let processedText = originalText;

        // Проверяем, какой режим отображения выбран
        if (this.currentView === 'uniqueness') {
            if (this.data.matched_sentences?.length > 0) {
                processedText = TextProcessor.highlightNonUniqueText(
                    originalText, this.data.matched_sentences
                );
            }
        } else if (this.currentView === 'spelling') {
            if (this.data.spelling_errors) {
                // Непосредственное выделение орфографических ошибок
                processedText = this.highlightSpellingErrors(
                    originalText, this.data.spelling_errors
                );
            }
        } else if (this.currentView === 'all') {
            // В режиме "Все" показываем и заимствования, и орфографические ошибки
            let tempText = originalText;

            if (this.data.matched_sentences?.length > 0) {
                tempText = TextProcessor.highlightNonUniqueText(
                    tempText, this.data.matched_sentences
                );
            }

            if (this.data.spelling_errors) {
                // Для комбинирования выделений используем DOM-манипуляции
                const tempDiv = document.createElement('div');
                tempDiv.innerHTML = tempText;

                // Находим все текстовые узлы
                const walker = document.createTreeWalker(
                    tempDiv,
                    NodeFilter.SHOW_TEXT,
                    null,
                    false
                );

                const textNodes = [];
                let node;
                while (node = walker.nextNode()) {
                    textNodes.push(node);
                }

                // Проверяем каждый текстовый узел на наличие орфографических ошибок
                for (const node of textNodes) {
                    const nodeText = node.nodeValue;
                    const parentNode = node.parentNode;

                    // Не обрабатываем уже выделенные фрагменты
                    if (parentNode.classList && parentNode.classList.contains('spelling-error')) {
                        continue;
                    }

                    // Ищем ошибки в этом текстовом узле
                    const nodeErrors = this.data.spelling_errors.filter(error => {
                        const errorStart = error.offset;
                        const errorEnd = errorStart + error.length;

                        // Получаем позицию узла в оригинальном тексте
                        let offset = 0;
                        let current = node;
                        while (current.previousSibling) {
                            if (current.previousSibling.nodeType === Node.TEXT_NODE) {
                                offset += current.previousSibling.nodeValue.length;
                            } else if (current.previousSibling.nodeType === Node.ELEMENT_NODE) {
                                offset += current.previousSibling.textContent.length;
                            }
                            current = current.previousSibling;
                        }

                        // Проверяем, находится ли ошибка в этом узле
                        return errorStart >= offset && errorEnd <= offset + nodeText.length;
                    });

                    if (nodeErrors.length > 0) {
                        // Создаем фрагмент с выделенными ошибками
                        const highlightedText = this.highlightSpellingErrors(nodeText, nodeErrors);
                        const fragment = document.createRange().createContextualFragment(highlightedText);
                        parentNode.replaceChild(fragment, node);
                    }
                }

                processedText = tempDiv.innerHTML;
            }
        }

        // Обновляем содержимое
        this.contentDiv.innerHTML = processedText;
    }

    // Вспомогательный метод для поиска текстовых узлов
    findTextNodes(element) {
        const walker = document.createTreeWalker(
            element,
            NodeFilter.SHOW_TEXT,
            null,
            false
        );

        const nodes = [];
        let node;
        while (node = walker.nextNode()) {
            nodes.push(node);
        }
        return nodes;
    }

    displayResults(data) {
        console.log("Полученные данные:", data);
        this.data = data;

        const uniqueness = parseFloat(data.overall_uniqueness).toFixed(2);
        const color = TextProcessor.getUniquenessColor(uniqueness);
        this.uniResultsDiv.innerHTML = `Уникальность: ${uniqueness}%`;
        this.uniResultsDiv.style.color = color;

        let outputHTML = '<h3>Результаты проверки на заимствования</h3>';

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

        const spamScore = parseFloat(data.spam_score).toFixed(2);
        const waterScore = parseFloat(data.water_score).toFixed(2);
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