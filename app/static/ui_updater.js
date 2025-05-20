import { MESSAGES, SPELLING_MESSAGES } from './constants.js';
import { TextProcessor } from './text_processor.js';
import { SpellingView } from './spelling_view.js';
import { UniquenessView } from './uniqueness_view.js';
import { SeoAnalysisView } from './seo_analysis_view.js';
import { AIAnalysisView } from './ai_analysis_view.js';
import { TextHighlightManager } from './text_highlight_manager.js';

/**
 * Класс для управления обновлением пользовательского интерфейса
 */
export class UIUpdater {
    /**
     * @constructor
     * @param {HTMLElement} resultsDiv - DOM элемент для основных результатов
     * @param {HTMLElement} uniResultsDiv - DOM элемент для результатов уникальности
     * @param {HTMLElement} seoResultsDiv - DOM элемент для результатов SEO
     * @param {HTMLElement} contentDiv - DOM элемент с текстом для анализа
     * @param {HTMLElement} aiResultsDiv - DOM элемент для результатов AI-анализа
     */
    constructor(resultsDiv, uniResultsDiv, seoResultsDiv, contentDiv, aiResultsDiv) {
        this.resultsDiv = resultsDiv;
        this.uniResultsDiv = uniResultsDiv;
        this.seoResultsDiv = seoResultsDiv;
        this.contentDiv = contentDiv;
        this.aiResultsDiv = aiResultsDiv;
        this.data = null;
        this.currentView = 'all';

        // Инициализируем представления для каждого типа анализа
        this.uniquenessView = new UniquenessView(this.uniResultsDiv, this.resultsDiv);
        this.seoAnalysisView = new SeoAnalysisView(this.seoResultsDiv);
        this.spellingView = new SpellingView(document.getElementById('spell-results'));
        this.aiAnalysisView = new AIAnalysisView(this.aiResultsDiv);

        // Добавляем CSS-стили для подсветки текста
        TextHighlightManager.ensureHighlightingStyles();
    }

    /**
     * Обновляет состояние загрузки интерфейса
     * @param {boolean} isLoading - Флаг загрузки
     */
    updateLoadingState(isLoading) {
        const loadingElement = document.getElementById('loading');
        if (isLoading) {
            loadingElement.style.display = 'block';
            this.resultsDiv.innerHTML = MESSAGES.LOADING;
        } else {
            loadingElement.style.display = 'none';
        }
    }

    /**
     * Переключает режим отображения
     * @param {string} viewType - Режим отображения ('all', 'uniqueness', 'spelling', 'ai', 'seo')
     */
    switchView(viewType) {
        console.log(`Переключение режима отображения на: ${viewType}`);
        this.currentView = viewType;

        // Подсветим активную вкладку
        this.highlightActiveTab(viewType);

        // Обновляем отображение текста при переключении представления
        this.updateTextDisplay();
    }

    /**
     * Подсвечивает активную вкладку
     * @private
     * @param {string} viewType - Режим отображения
     */
    highlightActiveTab(viewType) {
        // Находим все колонки и удаляем активный класс
        const columns = document.querySelectorAll('.info-column');
        columns.forEach(column => {
            column.classList.remove('active');
        });

        // Добавляем активный класс к выбранной колонке
        const activeColumn = document.querySelector(`.info-column[data-view="${viewType}"]`);
        if (activeColumn) {
            activeColumn.classList.add('active');
        }
    }

    /**
     * Обновляет отображение текста в соответствии с выбранным режимом
     */
    updateTextDisplay() {
        // Получаем оригинальный текст
        const originalText = this.contentDiv.dataset.originalText || this.contentDiv.textContent;

        // Журналируем для отладки
        console.log(`Режим отображения: ${this.currentView}`);

        // Если данных еще нет, просто отображаем экранированный текст
        if (!this.data) {
            console.log("Данных проверки нет, отображаем оригинальный текст");
            this.contentDiv.innerHTML = TextProcessor.escapeHtml(originalText);
            return;
        }

        // Применяем подсветку текста в соответствии с выбранным режимом
        const processedText = TextHighlightManager.applyHighlighting(originalText, this.data, this.currentView);

        // Обновляем содержимое
        this.contentDiv.innerHTML = processedText;
    }

    /**
     * Отображает результаты анализа
     * @param {Object} data - Данные о результатах анализа
     */
    displayResults(data) {
        console.log("Полученные данные:", data);
        this.data = data;

        // Проверка и установка значений по умолчанию для данных
        if (!this.data.matched_sentences) {
            this.data.matched_sentences = [];
        }
        if (!this.data.spelling_errors) {
            this.data.spelling_errors = [];
        }

        // Отображаем результаты проверки уникальности
        this.uniquenessView.displayResults(data);

        // Отображаем результаты SEO-анализа
        this.seoAnalysisView.displayResults(data);

        // Отображаем результаты AI-анализа
        if (data.ai_text_detected !== undefined || data.overall_ai_score !== undefined) {
            this.aiAnalysisView.displayResults(data);
        } else {
            this.aiResultsDiv.innerHTML = `<p class="ai-error">Данные анализа ИИ недоступны</p>`;
        }

        // Отображаем результаты проверки орфографии
        if (data.spelling_errors) {
            this.spellingView.displayResults(data.spelling_errors);
        } else {
            const spellingColumn = document.getElementById('spell-results');
            spellingColumn.innerHTML = `<p>${SPELLING_MESSAGES.NO_ERRORS}</p>`;
        }

        // Сохраняем оригинальный текст перед обновлением отображения
        if (!this.contentDiv.dataset.originalText) {
            this.contentDiv.dataset.originalText = this.contentDiv.textContent;
        }

        // После обновления данных обновляем отображение
        this.updateTextDisplay();
    }

    /**
     * Отображает ошибку
     * @param {Error|string} error - Ошибка для отображения
     */
    displayError(error) {
        const errorMessage = error instanceof Error ? error.message : String(error);
        this.resultsDiv.innerHTML = `Ошибка: ${TextProcessor.escapeHtml(errorMessage)}`;
    }
}