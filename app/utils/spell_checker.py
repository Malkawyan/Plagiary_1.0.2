from language_tool_python import LanguageTool
from typing import List, Dict, Union
import logging

logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)


def init_spell_checker(language='ru-RU'):
    """Инициализирует и возвращает экземпляр LanguageTool"""
    return LanguageTool(language)


def check_grammar_errors(text: str, tool: LanguageTool) -> List[Dict[str, Union[str, int]]]:
    """
    Проверяет текст только на грамматические ошибки (исключая орфографию).
    Совместим с разными версиями language-tool-python.
    """
    try:
        matches = tool.check(text)
        grammar_errors = []

        for match in matches:
            # Фильтруем только грамматические ошибки (исключая орфографию)
            if not match.ruleId.startswith('MORFOLOGIK_RULE_'):
                error_data = {
                    'word': text[match.offset:match.offset + match.errorLength],
                    'offset': match.offset,
                    'length': match.errorLength,
                    'message': match.message,
                    'replacements': match.replacements,
                    'rule_id': match.ruleId
                }

                # Добавляем описание правила (совместимость с разными версиями)
                if hasattr(match, 'ruleDescription'):
                    error_data['rule_description'] = match.ruleDescription
                elif hasattr(match, 'rule'):  # Для новых версий
                    error_data['rule_description'] = match.rule['description']

                grammar_errors.append(error_data)

        return grammar_errors
    except Exception as e:
        logging.error(f"Ошибка при проверке грамматики: {e}")
        return []


def highlight_grammar_errors_in_html(text: str, errors: List[Dict]) -> str:
    """
    Добавляет HTML-разметку для подсветки только слов с грамматическими ошибками.
    """
    if not errors:
        return text

    # Сортируем ошибки в обратном порядке, чтобы не сбивались индексы
    for error in sorted(errors, key=lambda x: x['offset'], reverse=True):
        start = error['offset']
        end = start + error['length']
        error_word = text[start:end]

        # Безопасное получение описания правила
        rule_desc = error.get('rule_description', 'Неизвестное правило')

        # Формируем подсказку с вариантами замены
        replacements_text = ", ".join(error["replacements"][:3]) if error["replacements"] else "нет вариантов"

        highlighted = (
            f'<span class="grammar-error" style="background-color: #ffcccc;" title="'
            f'Ошибка: {error["message"]}. '
            f'Правило: {rule_desc}. '
            f'Исправления: {replacements_text}">'
            f'{error_word}</span>'
        )
        text = text[:start] + highlighted + text[end:]

    return text


def format_grammar_errors_list(errors: List[Dict]) -> str:
    """
    Формирует HTML-список с найденными грамматическими ошибками.
    """
    if not errors:
        return "<p>Грамматических ошибок не обнаружено.</p>"

    result = '<div class="grammar-list">'
    for i, error in enumerate(errors, 1):
        replacements = ", ".join(error["replacements"][:3]) if error["replacements"] else "нет вариантов"
        rule_desc = error.get('rule_description', 'Неизвестное правило')

        result += f'''
        <div class="grammar-item">
            <span class="grammar-word">{error['word']}</span>: {error['message']}
            <br>Правило: {rule_desc}
            <br>Варианты: {replacements}
        </div>
        '''
    result += '</div>'
    return result


# Для обратной совместимости
check_text = check_grammar_errors