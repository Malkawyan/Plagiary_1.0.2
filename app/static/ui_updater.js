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

    // Полностью переработанный метод выделения орфографических ошибок
    highlightSpellingErrors(text, errors) {
        if (!errors || errors.length === 0 || !text) return this.constructor.safeTextContent(text);

        // Сначала экранируем текст для безопасного HTML
        const safeText = this.constructor.safeTextContent(text);

        // Создаем временный контейнер для HTML
        const tempContainer = document.createElement("div");
        tempContainer.innerHTML = safeText;

        // Получаем текстовые узлы для вставки разметки
        const allTextNodes = this.collectTextNodes(tempContainer);

        // Сортируем ошибки от последней к первой для сохранения корректных позиций
        const sortedErrors = [...errors].sort((a, b) => b.offset - a.offset);

        // Для каждой ошибки находим нужный текстовый узел и добавляем выделение
        for (const error of sortedErrors) {
            if (!error || typeof error.offset !== 'number' || !error.word) continue;

            const offset = error.offset;
            const length = error.length || error.word.length;
            if (length <= 0) continue;

            // Подготовим строку с заменами для всплывающей подсказки
            const replacements = error.replacements && error.replacements.length > 0
                ? error.replacements.slice(0, 3).join(', ')
                : 'нет вариантов';

            // Найдем текстовый узел, содержащий эту ошибку
            let currentPosition = 0;
            let targetNode = null;
            let relativeOffset = 0;

            for (const node of allTextNodes) {
                const nodeLength = node.nodeValue.length;

                if (offset >= currentPosition && offset < currentPosition + nodeLength) {
                    targetNode = node;
                    relativeOffset = offset - currentPosition;
                    break;
                }

                currentPosition += nodeLength;
            }

            // Если нашли подходящий узел, вставляем выделение
            if (targetNode) {
                const nodeText = targetNode.nodeValue;
                const errorEnd = Math.min(relativeOffset + length, nodeText.length);

                // Создаем 3 новых текстовых узла: до ошибки, ошибка с выделением, после ошибки
                const beforeError = nodeText.substring(0, relativeOffset);
                const errorText = nodeText.substring(relativeOffset, errorEnd);
                const afterError = nodeText.substring(errorEnd);

                const errorSpan = document.createElement('span');
                errorSpan.className = 'spelling-error';
                errorSpan.style.color = 'red';
                errorSpan.style.textDecoration = 'underline wavy red';
                errorSpan.title = `Варианты: ${replacements}`;
                errorSpan.textContent = errorText;

                const fragment = document.createDocumentFragment();
                if (beforeError) fragment.appendChild(document.createTextNode(beforeError));
                fragment.appendChild(errorSpan);
                if (afterError) fragment.appendChild(document.createTextNode(afterError));

                targetNode.parentNode.replaceChild(fragment, targetNode);
            }
        }

        return tempContainer.innerHTML;
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

            // Сначала применяем выделение неуникальных фрагментов
            if (this.data.matched_sentences?.length > 0) {
                tempText = TextProcessor.highlightNonUniqueText(
                    tempText, this.data.matched_sentences
                );
            }

            // Затем выделяем орфографические ошибки
            if (this.data.spelling_errors) {
                const tempDiv = document.createElement('div');
                tempDiv.innerHTML = tempText;

                // Обходим DOM-дерево и обрабатываем только текстовые узлы
                const textNodes = this.collectTextNodes(tempDiv);

                // Строим карту смещений для всех текстовых узлов
                let currentPosition = 0;
                const nodePositions = [];

                for (const node of textNodes) {
                    const nodeLength = node.nodeValue.length;
                    nodePositions.push({
                        node,
                        start: currentPosition,
                        end: currentPosition + nodeLength
                    });
                    currentPosition += nodeLength;
                }

                // Для каждой ошибки ищем соответствующий текстовый узел
                for (const error of this.data.spelling_errors) {
                    if (!error || typeof error.offset !== 'number' || !error.word) continue;

                    const errorStart = error.offset;
                    const errorLength = error.length || error.word.length;
                    const errorEnd = errorStart + errorLength;

                    // Ищем узел, содержащий эту ошибку
                    for (const {node, start, end} of nodePositions) {
                        // Если ошибка полностью находится в этом узле
                        if (errorStart >= start && errorEnd <= end) {
                            // Вычисляем относительные смещения внутри узла
                            const relativeStart = errorStart - start;
                            const relativeEnd = errorEnd - start;

                            const nodeText = node.nodeValue;
                            const errorWord = nodeText.substring(relativeStart, relativeEnd);

                            // Если слово имеет смысл выделять
                            if (errorWord && errorWord.trim() !== '') {
                                // Готовим замены для подсказки
                                const replacements = error.replacements && error.replacements.length > 0
                                    ? error.replacements.slice(0, 3).join(', ')
                                    : 'нет вариантов';

                                // Разбиваем текст на 3 части и создаем выделение
                                const beforeError = nodeText.substring(0, relativeStart);
                                const afterError = nodeText.substring(relativeEnd);

                                const errorSpan = document.createElement('span');
                                errorSpan.className = 'spelling-error';
                                errorSpan.style.color = 'red';
                                errorSpan.style.textDecoration = 'underline wavy red';
                                errorSpan.title = `Варианты: ${replacements}`;
                                errorSpan.textContent = errorWord;

                                const fragment = document.createDocumentFragment();
                                if (beforeError) fragment.appendChild(document.createTextNode(beforeError));
                                fragment.appendChild(errorSpan);
                                if (afterError) fragment.appendChild(document.createTextNode(afterError));

                                node.parentNode.replaceChild(fragment, node);

                                // Обновляем карту смещений после изменения DOM
                                break;
                            }
                        }
                    }
                }

                processedText = tempDiv.innerHTML;
            }
        }

        // Обновляем содержимое
        this.contentDiv.innerHTML = processedText;
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