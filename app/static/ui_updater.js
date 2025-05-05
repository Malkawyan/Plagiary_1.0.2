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
        this.data = null; // Сохраняем данные последнего ответа
        this.currentView = 'all'; // По умолчанию показываем все результаты
    }

    updateLoadingState(isLoading) {
        const loadingElement = document.getElementById('loading');
        if (isLoading) {
            // Показать анимацию загрузки
            loadingElement.style.display = 'block';
            this.resultsDiv.innerHTML = MESSAGES.LOADING;
        } else {
            // Скрыть анимацию загрузки, но НЕ сбрасывать содержимое resultsDiv
            loadingElement.style.display = 'none';
        }
    }

    displaySpellingResults(errors) {
        const spellingColumn = document.getElementById('spell-results');

        if (!errors || errors.length === 0) {
            spellingColumn.innerHTML = `<p style="font-family: 'Times New Roman', Times, serif; font-size: 11px;">${SPELLING_MESSAGES.NO_ERRORS}</p>`;
            return;
        }

        let html = `<div style="font-family: 'Times New Roman', Times, serif; font-size: 11px;">`;

        // Собираем только уникальные слова с ошибками
        const uniqueErrorWords = [...new Set(errors.map(error => error.word))];

        uniqueErrorWords.forEach(word => {
            html += `<span style="color: red;">${word}</span> `;
        });

        html += '</div>';
        spellingColumn.innerHTML = html;
    }

    highlightSpellingErrors(text, errors) {
        if (!errors || errors.length === 0) return text;

        // Сортируем в обратном порядке для корректной вставки
        const sortedErrors = [...errors].sort((a, b) => b.offset - a.offset);

        let result = text;
        for (const error of sortedErrors) {
            const start = error.offset;
            const end = start + error.length;
            const errorWord = result.slice(start, end);

            const highlighted = `<span style="color: red;">${errorWord}</span>`;
            result = result.slice(0, start) + highlighted + result.slice(end);
        }

        return result;
    }

    // Новый метод для переключения вида отображения
    switchView(viewType) {
        this.currentView = viewType;

        // Если у нас есть данные, то обновляем отображение текста
        if (this.data) {
            this.updateTextDisplay();
        }
    }

    // Обновление отображения текста в зависимости от выбранного вида
    updateTextDisplay() {
        // Сначала сбрасываем текст к оригинальному
        const originalText = this.contentDiv.textContent;

        // В зависимости от текущего вида, применяем разные подсветки
        if (this.currentView === 'uniqueness') {
            // Только подсветка заимствований
            if (this.data.matched_sentences && this.data.matched_sentences.length > 0) {
                this.contentDiv.innerHTML = TextProcessor.highlightNonUniqueText(
                    originalText, this.data.matched_sentences
                );
            } else {
                this.contentDiv.innerHTML = originalText;
            }
        } else if (this.currentView === 'spelling') {
            // Только подсветка орфографических ошибок
            if (this.data.spelling_errors) {
                this.contentDiv.innerHTML = this.highlightSpellingErrors(
                    originalText, this.data.spelling_errors
                );
            } else {
                this.contentDiv.innerHTML = originalText;
            }
        } else if (this.currentView === 'all') {
            // Полная подсветка - сначала заимствования, потом орфография
            let processedText = originalText;

            if (this.data.matched_sentences && this.data.matched_sentences.length > 0) {
                processedText = TextProcessor.highlightNonUniqueText(
                    processedText, this.data.matched_sentences
                );
            }

            if (this.data.spelling_errors) {
                processedText = this.highlightSpellingErrors(
                    processedText, this.data.spelling_errors
                ).replace(/&lt;/g, '<').replace(/&gt;/g, '>'); // Восстанавливаем HTML-теги после экранирования
            }

            this.contentDiv.innerHTML = processedText;
        } else {
            // Для других случаев (SEO, AI) - просто текст без подсветок
            this.contentDiv.innerHTML = originalText;
        }
    }

    displayResults(data) {
        console.log("Полученные данные:", data); // Для отладки

        // Сохраняем данные для последующего переключения режимов
        this.data = data;

        // 1. Обновляем блок с уникальностью (uni-results)
        const uniqueness = parseFloat(data.overall_uniqueness).toFixed(2);
        const color = TextProcessor.getUniquenessColor(uniqueness);
        this.uniResultsDiv.innerHTML = `Уникальность: ${uniqueness}%`;
        this.uniResultsDiv.style.color = color;

        // 2. Основной блок результатов (output) - информация о заимствованиях
        let outputHTML = '<h3>Результаты проверки на заимствования</h3>';

        if (data.file_similarity && Object.keys(data.file_similarity).length > 0) {
            outputHTML += '<h4>Найдены совпадения в файлах:</h4><ul>';

            for (const [filename, similarity] of Object.entries(data.file_similarity)) {
                // Округляем проценты совпадений до двух знаков после запятой
                const roundedSimilarity = parseFloat(similarity).toFixed(2);
                outputHTML += `<li>${filename}: ${roundedSimilarity}% совпадений</li>`;
            }

            outputHTML += '</ul>';
        } else {
            outputHTML += '<p>Прямые заимствования не обнаружены</p>';
        }

        this.resultsDiv.innerHTML = outputHTML;

        // 3. SEO-анализ (seo-results)
        const spamScore = parseFloat(data.spam_score).toFixed(2);
        const waterScore = parseFloat(data.water_score).toFixed(2);
        this.seoResultsDiv.innerHTML = `
            <p>Спамность: ${spamScore}%</p>
            <p>Водянистость: ${waterScore}%</p>
        `;

        // 4. ИИ-анализ (ai-results)
        if (data.ai_text_detected !== undefined) {
            let aiPercent = typeof data.ai_text_detected === 'string'
                ? parseFloat(data.ai_text_detected.replace('%', ''))
                : data.ai_text_detected;

            // Округляем до двух знаков после запятой
            aiPercent = parseFloat(aiPercent).toFixed(2);

            this.aiResultsDiv.innerHTML = `
                <div class="ai-detection-result">
                    <h4>Анализ ИИ-текста</h4>
                    <div class="ai-meter">
                        <div class="ai-meter-fill"
                             style="width: ${aiPercent}%;
                                    background: ${this.getAiColor(aiPercent)};">
                        </div>
                    </div>
                    <p class="ai-percentage">${aiPercent}% вероятность ИИ-генерации</p>
                </div>
            `;
        } else {
            this.aiResultsDiv.innerHTML = `<p class="ai-error">Данные анализа ИИ недоступны</p>`;
        }

        // 5. Проверка орфографии
        if (data.spelling_errors) {
            this.displaySpellingResults(data.spelling_errors);
        } else {
            const spellingColumn = document.getElementById('spell-results');
            spellingColumn.innerHTML = `<p>${SPELLING_MESSAGES.NO_ERRORS}</p>`;
        }

        // Отображаем текст в соответствии с текущим выбранным режимом
        this.updateTextDisplay();
    }

    displayError(error) {
        const errorMessage = error instanceof Error ? error.message : String(error);
        this.resultsDiv.innerHTML = `Ошибка: ${errorMessage}`;
    }

    getAiColor(percent) {
        percent = parseFloat(percent);
        if (percent < 30) return '#4CAF50'; // Зелёный
        if (percent < 70) return '#FFC107'; // Жёлтый
        return '#f44336'; // Красный
    }
}