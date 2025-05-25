import { TextProcessor } from './text_processor.js';

/**
 * Класс для отображения результатов проверки уникальности
 */
export class UniquenessView {
    /**
     * @constructor
     * @param {HTMLElement} uniquenessResultsDiv - DOM элемент для отображения результатов уникальности
     * @param {HTMLElement} mainResultsDiv - DOM элемент для отображения детальных результатов
     */
    constructor(uniquenessResultsDiv, mainResultsDiv) {
        this.uniquenessResultsDiv = uniquenessResultsDiv;
        this.mainResultsDiv = mainResultsDiv;
    }

    /**
     * Отображает результаты проверки уникальности
     * @param {Object} data - Данные о результатах проверки уникальности
     */
    displayResults(data) {
        if (!data) return;

        // Отображаем основной процент уникальности
        const uniqueness = parseFloat(data.overall_uniqueness).toFixed(2);
        const color = TextProcessor.getUniquenessColor(uniqueness);
        this.uniquenessResultsDiv.innerHTML = `Уникальность: ${uniqueness}%`;
        this.uniquenessResultsDiv.style.color = color;

        // Отображаем детальную информацию
        let outputHTML = '<h3>Результаты проверки на заимствования</h3>';

        // Добавляем информацию о количестве найденных неуникальных фрагментов
        const matchedSentencesCount = data.matched_sentences ? data.matched_sentences.length : 0;
        outputHTML += `<p>Найдено неуникальных фрагментов: ${matchedSentencesCount}</p>`;

        // Отображаем информацию о совпадениях с файлами
        if (data.file_similarity && Object.keys(data.file_similarity).length > 0) {
            // Сортируем файлы по проценту заимствования в убывающем порядке
            const sortedFiles = Object.entries(data.file_similarity)
                .sort(([,a], [,b]) => parseFloat(b) - parseFloat(a))
                .slice(0, 7); // Берем только первые 7 файлов

            outputHTML += '<h4>Найдены совпадения в файлах (топ-7):</h4><ul>';

            for (const [filename, similarity] of sortedFiles) {
                const roundedSimilarity = parseFloat(similarity).toFixed(2);
                outputHTML += `<li>${TextProcessor.escapeHtml(filename)}: ${roundedSimilarity}% совпадений</li>`;
            }

            outputHTML += '</ul>';

            // Если файлов больше 7, добавляем информацию об этом
            const totalFiles = Object.keys(data.file_similarity).length;
            if (totalFiles > 7) {
                outputHTML += `<p class="additional-files-info">И еще ${totalFiles - 7} файл(ов) с меньшим процентом заимствования</p>`;
            }
        } else {
            outputHTML += '<p>Прямые заимствования не обнаружены</p>';
        }

        this.mainResultsDiv.innerHTML = outputHTML;
    }
}