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

        // Добавляем статистику анализа
        if (data.text_statistics) {
            const stats = data.text_statistics;
            outputHTML += `
                <div class="text-statistics">
                    <p><strong>Статистика анализа:</strong></p>
                    <ul>
                        <li>Всего предложений: ${stats.total_sentences}</li>
                        <li>Всего символов: ${stats.total_chars}</li>
                        <li>Всего слов: ${stats.total_words}</li>
                        <li>Заимствованных предложений: ${stats.borrowed_sentences_count}</li>
                    </ul>
                </div>
            `;
        }

        // Добавляем информацию о типе расчета
        outputHTML += `
            <div class="calculation-info">
                <p><em>💡 Уникальность рассчитывается с учетом объема заимствованного текста,
                а не только количества похожих предложений</em></p>
            </div>
        `;

        // Отображаем информацию о совпадениях с файлами
        if (data.file_similarity && Object.keys(data.file_similarity).length > 0) {
            // Сортируем файлы по проценту заимствования в убывающем порядке
            const sortedFiles = Object.entries(data.file_similarity)
                .sort(([,a], [,b]) => parseFloat(b) - parseFloat(a))
                .slice(0, 7); // Берем только первые 7 файлов

            outputHTML += '<h4>Обнаружены заимствования из файлов (топ-7 по объему):</h4><ul>';

            for (const [filename, borrowingPercentage] of sortedFiles) {
                const roundedPercentage = parseFloat(borrowingPercentage).toFixed(2);
                // Определяем уровень заимствования для цветовой индикации
                let levelClass = 'low-borrowing';
                let levelText = '(низкий)';

                if (roundedPercentage >= 15) {
                    levelClass = 'high-borrowing';
                    levelText = '(высокий)';
                } else if (roundedPercentage >= 5) {
                    levelClass = 'medium-borrowing';
                    levelText = '(средний)';
                }

                outputHTML += `
                    <li class="${levelClass}">
                        ${TextProcessor.escapeHtml(filename)}:
                        <strong>${roundedPercentage}%</strong> заимствованного текста
                        <span class="borrowing-level">${levelText}</span>
                    </li>
                `;
            }

            outputHTML += '</ul>';

            // Если файлов больше 7, добавляем информацию об этом
            const totalFiles = Object.keys(data.file_similarity).length;
            if (totalFiles > 7) {
                outputHTML += `<p class="additional-files-info">И еще ${totalFiles - 7} файл(ов) с меньшим объемом заимствований</p>`;
            }

            // Добавляем пояснение к новой системе подсчета
            outputHTML += `
                <div class="explanation">
                    <p><strong>Как читать результаты:</strong></p>
                    <ul>
                        <li>Проценты показывают долю вашего текста, заимствованную из каждого файла</li>
                        <li>Учитывается не только количество похожих предложений, но и их объем</li>
                        <li>Степень похожести влияет на итоговый процент заимствования</li>
                    </ul>
                </div>
            `;
        } else {
            outputHTML += '<p>Прямые заимствования не обнаружены</p>';
        }

        // Добавляем CSS стили для новых элементов
        if (!document.getElementById('uniqueness-styles')) {
            const styleElement = document.createElement('style');
            styleElement.id = 'uniqueness-styles';
            styleElement.textContent = `
                .text-statistics {
                    background-color: #f8f9fa;
                    padding: 10px;
                    border-radius: 5px;
                    margin: 10px 0;
                }
                .calculation-info {
                    background-color: #e7f3ff;
                    padding: 8px;
                    border-radius: 5px;
                    margin: 10px 0;
                    border-left: 4px solid #2196F3;
                }
                .low-borrowing { color: #28a745; }
                .medium-borrowing { color: #ffc107; }
                .high-borrowing { color: #dc3545; }
                .borrowing-level {
                    font-size: 0.9em;
                    opacity: 0.8;
                }
                .explanation {
                    background-color: #fff3cd;
                    padding: 10px;
                    border-radius: 5px;
                    margin: 15px 0;
                    border-left: 4px solid #ffc107;
                }
                .explanation ul {
                    margin: 5px 0 0 20px;
                }
                .additional-files-info {
                    font-style: italic;
                    color: #6c757d;
                    margin-top: 10px;
                }
            `;
            document.head.appendChild(styleElement);
        }

        this.mainResultsDiv.innerHTML = outputHTML;
    }
}