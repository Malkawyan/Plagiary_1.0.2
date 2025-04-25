import { MESSAGES } from './constants.js';
import { TextProcessor } from './text_processor.js';

export class UIUpdater {
    constructor(resultsDiv, uniResultsDiv, seoResultsDiv, contentDiv, aiResultsDiv) {
        this.resultsDiv = resultsDiv;
        this.uniResultsDiv = uniResultsDiv;
        this.seoResultsDiv = seoResultsDiv;
        this.contentDiv = contentDiv;
        this.aiResultsDiv = aiResultsDiv;
    }

    updateLoadingState(isLoading) {
        if (isLoading) {
            this.resultsDiv.innerHTML = MESSAGES.LOADING;
        } else {
            this.resultsDiv.innerHTML = MESSAGES.DEFAULT_RESULTS;
        }
    }

    displayResults(data) {

        console.log("[DEBUG] AI Detection Data:", {
            received: data.hasOwnProperty('ai_text_detected'),
            value: data.ai_text_detected,
            type: typeof data.ai_text_detected
        });

        const uniqueness = parseFloat(data.overall_uniqueness);
        const color = TextProcessor.getUniquenessColor(uniqueness);

        // Обновление блока с уникальностью
        this.uniResultsDiv.innerHTML = `Уникальность: ${uniqueness}%`;
        this.uniResultsDiv.style.color = color;
        this.resultsDiv.style.color = color;

        // Подсветка неуникальных фрагментов в тексте
        if (data.matched_sentences && data.matched_sentences.length > 0) {
            this.contentDiv.innerHTML = TextProcessor.highlightNonUniqueText(
                this.contentDiv.textContent,
                data.matched_sentences
            );
        }

        console.log('API Response:', data);
        // Обновляем результаты плагиата
        this.updatePlagiarismResults(data);

        // Обновление SEO-анализа
        this.seoResultsDiv.innerHTML = `
            <p>Спамность: ${data.spam_score}%</p>
            <p>Водянистость: ${data.water_score}%</p>
        `;

        /// Блок ИИ-анализа
        if (data.ai_text_detected !== undefined) {
            const aiPercent = typeof data.ai_text_detected === 'string'
                ? parseFloat(data.ai_text_detected.replace('%', ''))
                : data.ai_text_detected;

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

    }

    updatePlagiarismResults(data) {
            console.log('[DEBUG] updatePlagiarismResults called with data:', data);

            if (!this.resultsDiv) {
                console.error('resultsDiv is not defined!');
                return;
            }

            console.log('Current resultsDiv content:', this.resultsDiv.innerHTML);

            let resultsHTML = '<h3>Результаты проверки:</h3>';

            if (data.file_similarity) {
                console.log('file_similarity exists:', data.file_similarity);
            } else {
                console.log('file_similarity is MISSING in response');
            }

            this.resultsDiv.insertAdjacentHTML('beforeend', resultsHTML);
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