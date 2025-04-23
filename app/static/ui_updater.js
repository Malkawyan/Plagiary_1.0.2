import { MESSAGES } from './constants.js';
import { TextProcessor } from './text_processor.js';

export class UIUpdater {
    constructor(resultsDiv, uniResultsDiv, seoResultsDiv, contentDiv) {
        this.resultsDiv = resultsDiv;
        this.uniResultsDiv = uniResultsDiv;
        this.seoResultsDiv = seoResultsDiv;
        this.contentDiv = contentDiv;
    }

    updateLoadingState(isLoading) {
        if (isLoading) {
            this.resultsDiv.innerHTML = MESSAGES.LOADING;
        } else {
            this.resultsDiv.innerHTML = MESSAGES.DEFAULT_RESULTS;
        }
    }

    displayResults(data) {
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
}