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
        const spellingColumn = document.querySelector('.info-column:nth-child(2) .output-container');

        if (!errors || errors.length === 0) {
            spellingColumn.innerHTML = `<p>${SPELLING_MESSAGES.NO_ERRORS}</p>`;
            return;
        }

        let html = `<h4>${SPELLING_MESSAGES.ERRORS_FOUND}</h4><div class="spelling-list">`;

        errors.forEach(error => {
            html += `
                <div class="spelling-item">
                    <span class="spelling-word">${error.word}</span>:
                    ${error.message}. ${SPELLING_MESSAGES.SUGGESTIONS} ${error.replacements.join(', ')}
                </div>
            `;
        });

        html += '</div>';
        spellingColumn.innerHTML = html;
    }

    displayResults(data) {
        console.log("Полученные данные:", data); // Для отладки

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

            // Подсветка ошибок в тексте
            this.contentDiv.innerHTML = this.highlightSpellingErrors(
                this.contentDiv.textContent,
                data.spelling_errors
            );
        } else {
            const spellingColumn = document.querySelector('.info-column:nth-child(2) .output-container');
            spellingColumn.innerHTML = `<p>${SPELLING_MESSAGES.NO_ERRORS}</p>`;
        }

        // 6. Подсветка текста (если нужно)
        if (data.matched_sentences && data.matched_sentences.length > 0) {
            const currentContent = this.contentDiv.innerHTML; // Сохраняем уже подсвеченные орф. ошибки
            this.contentDiv.innerHTML = TextProcessor.highlightNonUniqueText(
                this.contentDiv.textContent,
                data.matched_sentences
            );
        }

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