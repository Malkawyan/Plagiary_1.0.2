import { TextProcessor } from './text_processor.js';

/**
 * Класс для отображения результатов анализа текста на AI-генерацию
 */
export class AIAnalysisView {
    /**
     * @constructor
     * @param {HTMLElement} aiResultsDiv - DOM элемент для отображения результатов AI-анализа
     */
    constructor(aiResultsDiv) {
        this.aiResultsDiv = aiResultsDiv;
    }

    /**
     * Отображает результаты проверки на генерацию искусственным интеллектом
     * @param {Object} data - Данные о результатах AI-анализа
     */
    displayResults(data) {
        if (!data) {
            this.aiResultsDiv.innerHTML = `<p class="ai-error">Данные анализа ИИ недоступны</p>`;
            return;
        }

        if (data.ai_text_detected !== undefined || data.overall_ai_score !== undefined) {
            // Определяем процент AI-генерации
            let aiPercent = data.overall_ai_score ||
                           (typeof data.ai_text_detected === 'string' ?
                            parseFloat(data.ai_text_detected.replace('%', '')) :
                            data.ai_text_detected);

            // Калибровка отображения для современных ИИ
            aiPercent = Math.min(100, parseFloat(aiPercent) * 1.15).toFixed(2);

            // Формируем HTML для отображения стилистических особенностей
            let featuresHtml = this.generateStylisticFeaturesHTML(data);

            // Формируем HTML для отображения анализа по чанкам
            let chunksHtml = this.generateChunksHTML(data);

            // Собираем полный HTML
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
        } else {
            this.aiResultsDiv.innerHTML = `<p class="ai-error">Данные анализа ИИ недоступны</p>`;
        }
    }

    /**
     * Генерирует HTML для отображения стилистических особенностей текста
     * @private
     * @param {Object} data - Данные о результатах AI-анализа
     * @returns {string} - HTML с информацией о стилистических особенностях
     */
    generateStylisticFeaturesHTML(data) {
        if (!data.stylistic_features) return '';

        return `
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

    /**
     * Генерирует HTML для отображения анализа по чанкам
     * @private
     * @param {Object} data - Данные о результатах AI-анализа
     * @returns {string} - HTML с информацией о анализе по чанкам
     */
    generateChunksHTML(data) {
        if (!data.chunks || data.chunks.length === 0) return '';

        let chunksHtml = '<div class="ai-detection-chunks"><h4>Анализ по фрагментам:</h4>';

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
        return chunksHtml;
    }

    /**
     * Определяет уровень уверенности модели в зависимости от процента
     * @private
     * @param {number|string} percent - Процент AI-генерации
     * @returns {string} - Текстовое описание уровня уверенности
     */
    getConfidenceLevel(percent) {
        percent = parseFloat(percent);
        if (percent < 20 || percent > 80) return "Высокая";
        if (percent < 30 || percent > 70) return "Средняя";
        return "Низкая";
    }

    /**
     * Определяет цвет для отображения процента AI-генерации
     * @private
     * @param {number|string} percent - Процент AI-генерации
     * @returns {string} - CSS-цвет
     */
    getAiColor(percent) {
        percent = parseFloat(percent);
        if (percent < 30) return '#4CAF50';
        if (percent < 70) return '#FFC107';
        return '#f44336';
    }
}