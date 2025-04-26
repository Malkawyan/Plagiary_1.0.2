from language_tool_python import LanguageTool
from typing import List, Dict, Union
import logging


def init_spell_checker(language='ru-RU'):
    """Инициализирует и возвращает экземпляр LanguageTool"""
    return LanguageTool(language)


def check_text(text: str, tool: LanguageTool) -> List[Dict[str, Union[str, int]]]:
    """
    Проверяет текст на орфографические ошибки.

    Args:
        text (str): Текст для проверки
        tool (LanguageTool): Экземпляр LanguageTool

    Returns:
        List[Dict]: Список ошибок с информацией о позиции и возможных исправлениях
    """
    try:
        matches = tool.check(text)
        return [
            {
                'word': text[match.offset:match.offset + match.errorLength],
                'offset': match.offset,
                'length': match.errorLength,
                'message': match.message,
                'replacements': match.replacements
            }
            for match in matches
        ]
    except Exception as e:
        logging.error(f"Ошибка при проверке орфографии: {e}")
        return []


def highlight_errors_in_html(text: str, errors: List[Dict]) -> str:
    """
    Добавляет HTML-разметку для подсветки ошибок в тексте.

    Args:
        text (str): Исходный текст
        errors (List[Dict]): Список ошибок из check_text()

    Returns:
        str: Текст с HTML-разметкой для подсветки ошибок
    """
    if not errors:
        return text

    # Сортируем в обратном порядке для корректной вставки
    for error in sorted(errors, key=lambda x: x['offset'], reverse=True):
        start = error['offset']
        end = start + error['length']
        error_word = text[start:end]

        highlighted = (
            f'<span class="spelling-error" title="'
            f'{error["message"]}. '
            f'Варианты исправления: {", ".join(error["replacements"][:3])}">'
            f'{error_word}</span>'
        )
        text = text[:start] + highlighted + text[end:]

    return text