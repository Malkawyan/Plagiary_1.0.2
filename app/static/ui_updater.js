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
        this.filteredSpellingErrors = []; // Храним отфильтрованные ошибки
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

    // Проверяет, является ли слово самостоятельным (не частью другого слова)
    isStandaloneWord(error, text) {
        const offset = error.offset;
        const word = error.word;
        const charBefore = offset > 0 ? text[offset - 1] : ' ';
        const charAfter = offset + word.length < text.length ? text[offset + word.length] : ' ';

        // Слово стоит отдельно, если до и после него НЕ буква/цифра
        return !this.isWordChar(charBefore) && !this.isWordChar(charAfter);
    }

    isWordChar(char) {
        return /[a-zA-Zа-яА-Я0-9]/.test(char); // Буквы и цифры
    }

    // Проверяет, является ли символ частью слова
    isWordChar(char) {
        return /[\p{L}\p{N}]/u.test(char); // Включает буквы и цифры всех языков
    }

    // Фильтрует ошибки по заданным критериям
    filterSpellingErrors(errors, text) {
        if (!errors || errors.length === 0) return [];

        return errors.filter(error => {
            // Проверяем, что слово не часть другого слова
            const isStandalone = this.isStandaloneWord(error, text);
            // Игнорируем слишком короткие "ошибки" (возможно, аббревиатуры)
            const isNotTooShort = error.word.length > 2;
            return isStandalone && isNotTooShort;
        });
    }

    // Группирует уникальные ошибки по словам
    groupUniqueErrors(filteredErrors) {
        if (!filteredErrors || filteredErrors.length === 0) return [];

        const uniqueErrorWords = {};

        filteredErrors.forEach(error => {
            const word = error.word;
            if (!uniqueErrorWords[word]) {
                uniqueErrorWords[word] = error;
            }
        });

        return Object.values(uniqueErrorWords);
    }

    displaySpellingResults(errors) {
        const spellingColumn = document.getElementById('spell-results');

        if (!errors || errors.length === 0) {
            spellingColumn.innerHTML = `<p style="font-family: 'Times New Roman', Times, serif; font-size: 11px;">${SPELLING_MESSAGES.NO_ERRORS}</p>`;
            return;
        }

        // Используем уже отфильтрованные ошибки
        const uniqueErrors = this.groupUniqueErrors(this.filteredSpellingErrors);

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

    highlightSpellingErrors(text, errors) {
        if (!errors || errors.length === 0) return TextProcessor.escapeHtml(text);

        // Экранируем текст и запоминаем изменения длины
        const escapedText = TextProcessor.escapeHtml(text);
        const escapeDiff = escapedText.length - text.length;

        // Если экранирование не изменило длину (нет спецсимволов), работаем как раньше
        if (escapeDiff === 0) {
            const sortedErrors = [...errors].sort((a, b) => b.offset - a.offset);
            let result = escapedText;

            for (const error of sortedErrors) {
                const start = error.offset;
                const end = start + error.length;
                const errorWord = result.slice(start, end);
                const replacements = error.replacements?.slice(0, 3).join(', ') || 'нет вариантов';

                result = result.slice(0, start) +
                         `<span class="spelling-error" title="Варианты: ${replacements}" style="color: red;">${errorWord}</span>` +
                         result.slice(end);
            }
            return result;
        }

        // Иначе пересчитываем позиции ошибок с учетом экранирования
        const adjustedErrors = errors.map(error => {
            let newOffset = error.offset;
            let newLength = error.length;

            // Проходим по тексту до ошибки и считаем, насколько сместились символы
            let cumulativeOffset = 0;
            for (let i = 0; i < error.offset; i++) {
                const char = text[i];
                const escapedChar = TextProcessor.escapeHtml(char);
                cumulativeOffset += escapedChar.length - 1; // Насколько увеличилась позиция
            }
            newOffset += cumulativeOffset;

            // Корректируем длину ошибки (если внутри есть экранированные символы)
            let lengthAdjustment = 0;
            for (let i = error.offset; i < error.offset + error.length; i++) {
                const char = text[i];
                const escapedChar = TextProcessor.escapeHtml(char);
                lengthAdjustment += escapedChar.length - 1;
            }
            newLength += lengthAdjustment;

            return {
                ...error,
                offset: newOffset,
                length: newLength,
            };
        });

        // Сортируем ошибки от конца к началу, чтобы вставка не ломала позиции
        const sortedErrors = adjustedErrors.sort((a, b) => b.offset - a.offset);
        let result = escapedText;

        // Вставляем подсветку ошибок
        for (const error of sortedErrors) {
            const start = error.offset;
            const end = start + error.length;
            const errorWord = result.slice(start, end);
            const replacements = error.replacements?.slice(0, 3).join(', ') || 'нет вариантов';

            result = result.slice(0, start) +
                     `<span class="spelling-error" title="Варианты: ${replacements}" style="color: red;">${errorWord}</span>` +
                     result.slice(end);
        }

        return result;
    }

    switchView(viewType) {
        this.currentView = viewType;
        if (this.data) {
            this.updateTextDisplay();
        }
    }

    updateTextDisplay() {
        const originalText = this.contentDiv.textContent;

        // Начинаем всегда с экранированного текста
        let processedText = TextProcessor.escapeHtml(originalText);

        if (this.currentView === 'uniqueness') {
            if (this.data.matched_sentences && this.data.matched_sentences.length > 0) {
                processedText = TextProcessor.highlightNonUniqueText(
                    originalText, this.data.matched_sentences
                );
            }
        } else if (this.currentView === 'spelling') {
            if (this.data.spelling_errors) {
                processedText = this.highlightSpellingErrors(
                    originalText, this.data.spelling_errors
                );
            }
        } else if (this.currentView === 'all') {
            // Создаем массив маркеров для применения выделений
            let markers = [];

            // Добавляем маркеры неуникальных фрагментов
            if (this.data.matched_sentences && this.data.matched_sentences.length > 0) {
                this.data.matched_sentences.forEach(sentence => {
                    markers.push({
                        start: sentence.start_pos,
                        end: sentence.end_pos,
                        type: 'uniqueness',
                        data: sentence
                    });
                });
            }

            // Добавляем маркеры орфографических ошибок (используем фильтрованный список)
            if (this.filteredSpellingErrors && this.filteredSpellingErrors.length > 0) {
                this.filteredSpellingErrors.forEach(error => {
                    markers.push({
                        start: error.offset,
                        end: error.offset + error.length,
                        type: 'spelling',
                        data: error
                    });
                });
            }

            // Сортируем маркеры по их позиции в тексте (от конца к началу)
            markers.sort((a, b) => b.start - a.start);

            // Применяем все маркеры
            for (const marker of markers) {
                const start = marker.start;
                const end = marker.end;

                if (marker.type === 'uniqueness') {
                    const fragment = TextProcessor.escapeHtml(originalText.slice(start, end));
                    const source = marker.data.source ? TextProcessor.escapeHtml(marker.data.source) : '';
                    const highlighted = `<span class="non-unique" title="Источник: ${source}" style="background-color: #ffe6e6;">${fragment}</span>`;
                    processedText = processedText.slice(0, start) + highlighted + processedText.slice(end);
                } else if (marker.type === 'spelling') {
                    const errorWord = TextProcessor.escapeHtml(originalText.slice(start, end));
                    const replacements = marker.data.replacements && marker.data.replacements.length > 0
                        ? marker.data.replacements.slice(0, 3).map(r => TextProcessor.escapeHtml(r)).join(', ')
                        : 'нет вариантов';

                    const highlighted = `<span class="spelling-error" title="Варианты: ${replacements}" style="color: red;">${errorWord}</span>`;
                    processedText = processedText.slice(0, start) + highlighted + processedText.slice(end);
                }
            }
        }

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
            // Фильтруем и сохраняем список ошибок при первой загрузке данных
            const originalText = this.contentDiv.textContent;
            this.filteredSpellingErrors = this.filterSpellingErrors(data.spelling_errors, originalText);
            this.displaySpellingResults(this.filteredSpellingErrors);
        } else {
            const spellingColumn = document.getElementById('spell-results');
            spellingColumn.innerHTML = `<p>${SPELLING_MESSAGES.NO_ERRORS}</p>`;
            this.filteredSpellingErrors = [];
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