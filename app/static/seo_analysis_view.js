/**
 * Класс для отображения результатов SEO-анализа
 */
export class SeoAnalysisView {
    /**
     * @constructor
     * @param {HTMLElement} seoResultsDiv - DOM элемент для отображения результатов SEO-анализа
     */
    constructor(seoResultsDiv) {
        this.seoResultsDiv = seoResultsDiv;
    }

    /**
     * Отображает результаты SEO-анализа
     * @param {Object} data - Данные о результатах SEO-анализа
     */
    displayResults(data) {
        if (!data) {
            this.seoResultsDiv.innerHTML = '<p>Данные SEO-анализа недоступны</p>';
            return;
        }

        const spamScore = parseFloat(data.spam_score || 0).toFixed(2);
        const waterScore = parseFloat(data.water_score || 0).toFixed(2);

        let html = `
            <p>Спамность: ${spamScore}%</p>
            <p>Водянистость: ${waterScore}%</p>
        `;

        // Если есть дополнительные SEO-метрики, добавляем их
        if (data.keyword_density) {
            html += '<h4>Плотность ключевых слов:</h4><ul>';

            for (const [keyword, density] of Object.entries(data.keyword_density)) {
                html += `<li>${keyword}: ${parseFloat(density).toFixed(2)}%</li>`;
            }

            html += '</ul>';
        }

        this.seoResultsDiv.innerHTML = html;
    }
}