from language_tool_python import LanguageTool
from typing import List, Dict, Union
import re
import logging
import json
import os

# Настройка логгирования
logging.basicConfig(level=logging.INFO)
# Уменьшаем вывод от urllib3
logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)


def init_spell_checker(language='ru-RU'):
    """Инициализация LanguageTool для проверки орфографии"""
    tool = LanguageTool(language)

    # Включаем больше правил, связанных с орфографией
    # Отключаем только те категории, которые однозначно не связаны с орфографией
    disabled_rule_categories = [
        'PUNCTUATION', 'TYPOGRAPHY', 'CASING'
    ]

    # Пытаемся отключить неорфографические правила
    for rule in disabled_rule_categories:
        try:
            tool.disable(rule)
        except:
            logging.warning(f"Не удалось отключить правило {rule}")

    return tool


def check_spelling_errors(text: str, tool: LanguageTool) -> List[Dict[str, Union[str, int]]]:
    """
    Проверка текста на наличие орфографических ошибок с помощью LanguageTool

    Args:
        text: Текст для проверки
        tool: Инициализированный экземпляр LanguageTool

    Returns:
        Список словарей с информацией об ошибках
    """
    spelling_errors = []

    # Проверяем текст с помощью LanguageTool
    try:
        matches = tool.check(text)
        if not matches:
            logging.info("LanguageTool не нашел ошибок или предупреждений")
    except Exception as e:
        logging.error(f"Ошибка при проверке текста: {e}")
        return []

    # Обрабатываем найденные ошибки
    for match in matches:
        rule_id = match.ruleId
        error_text = text[match.offset:match.offset + match.errorLength]

        # Лог для отладки - показывает все найденные правила
        logging.debug(f"Найдено правило: {rule_id} для текста: {error_text}")

        # Расширяем критерии включения для охвата большего числа ошибок
        # Проверяем, связана ли ошибка с орфографией или грамматикой
        if ('SPELL' in rule_id.upper() or 'TYPO' in rule_id.upper() or
                'MORFOLOGIK' in rule_id.upper() or 'GRAMMAR' in rule_id.upper()):
            error_data = {
                'word': error_text,
                'offset': match.offset,
                'length': match.errorLength,
                'message': getattr(match, 'message', "Возможная орфографическая ошибка"),
                'replacements': getattr(match, 'replacements', [])
            }
            spelling_errors.append(error_data)

    # Доп. проверка на короткие слова и аббревиатуры
    final_errors = []
    for error in spelling_errors:
        word = error['word'].lower()

        # Пропускаем очень короткие слова (вероятно, аббревиатуры)
        if len(word) <= 2:
            continue

        # Добавляем только слова с высокой вероятностью ошибки
        final_errors.append(error)

    # Сортируем ошибки по их позиции в тексте
    final_errors.sort(key=lambda x: x['offset'])

    return final_errors


def highlight_spelling_errors_in_html(text: str, errors: List[Dict]) -> str:
    """
    Добавляет HTML-разметку для выделения слов с орфографическими ошибками

    Args:
        text: Исходный текст
        errors: Список словарей с ошибками

    Returns:
        HTML-текст с выделенными ошибками
    """
    if not errors:
        return text

    # Работаем с копией текста
    result = text

    # Сортируем ошибки в обратном порядке, чтобы избежать смещения индексов
    for error in sorted(errors, key=lambda x: x['offset'], reverse=True):
        start = error['offset']
        end = start + error['length']
        error_word = result[start:end]

        # Форматируем предложения замены
        replacements = ", ".join(error["replacements"][:3]) if error["replacements"] else "нет предложений"

        # Создаем HTML-разметку для выделения
        highlight = f'<span class="spelling-error" style="background-color: #ffcccc;" title="Ошибка: {error["message"]}. Предложения: {replacements}">{error_word}</span>'

        # Заменяем в тексте
        result = result[:start] + highlight + result[end:]

    return result