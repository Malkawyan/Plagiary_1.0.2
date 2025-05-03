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
    Добавляет HTML-разметку для подсветки только грамматических ошибок.
    """
    if not errors:
        return text

    for error in sorted(errors, key=lambda x: x['offset'], reverse=True):
        start = error['offset']
        end = start + error['length']
        error_word = text[start:end]

        # Безопасное получение описания правила
        rule_desc = error.get('rule_description', 'Неизвестное правило')

        highlighted = (
            f'<span class="grammar-error" style="background-color: #ffcccc;" title="'
            f'Грамматическая ошибка: {error["message"]}. '
            f'Правило: {rule_desc}. '
            f'Варианты исправления: {", ".join(error["replacements"][:3])}">'
            f'{error_word}</span>'
        )
        text = text[:start] + highlighted + text[end:]

    return text


# Для обратной совместимости
check_text = check_grammar_errors