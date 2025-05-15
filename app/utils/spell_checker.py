from language_tool_python import LanguageTool
from typing import List, Dict, Union
import logging
import re

logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)


def init_spell_checker(language='ru-RU'):
    """
    Инициализирует и возвращает экземпляр LanguageTool с расширенными настройками для русского языка
    """
    tool = LanguageTool(language)

    # Устанавливаем максимальную чувствительность для проверки орфографии
    try:
        # Этот метод может быть доступен в некоторых версиях LanguageTool
        if hasattr(tool, 'setMaxSpellingSuggestions'):
            tool.setMaxSpellingSuggestions(10)  # Увеличиваем количество предложений

        # Другие возможные настройки (зависит от версии библиотеки)
        if hasattr(tool, 'disable'):
            # Отключаем некоторые правила грамматики, чтобы сфокусироваться только на орфографии
            grammar_rules = ['PUNCTUATION', 'TYPOGRAPHY', 'STYLE']
            for rule in grammar_rules:
                try:
                    tool.disable(rule)
                except:
                    pass
    except Exception as e:
        logging.warning(f"Не удалось настроить дополнительные параметры LanguageTool: {e}")

    return tool


def check_spelling_errors(text: str, tool: LanguageTool) -> List[Dict[str, Union[str, int]]]:
    """
    Комплексная проверка текста на орфографические ошибки.
    Включает несколько стратегий обнаружения ошибок.
    """
    try:
        spelling_errors = []

        # Получаем результаты проверки от LanguageTool
        matches = tool.check(text)

        # Создаем словарь слов из текста для дополнительного анализа
        words = re.findall(r'[\w\-]+', text)
        word_positions = {}

        # Находим позиции всех слов в тексте
        for word in words:
            positions = []
            for match in re.finditer(r'\b' + re.escape(word) + r'\b', text):
                positions.append(match.start())
            word_positions[word] = positions

        # 1. Собираем орфографические ошибки из LanguageTool
        for match in matches:
            error_text = text[match.offset:match.offset + match.errorLength]

            # Получаем идентификатор правила и описание
            rule_id = match.ruleId
            rule_desc = ""
            if hasattr(match, 'ruleDescription'):
                rule_desc = match.ruleDescription.lower()
            elif hasattr(match, 'rule') and 'description' in match.rule:
                rule_desc = match.rule['description'].lower()

            # Расширенный список префиксов для проверки
            is_spelling_error = any([
                rule_id.startswith('MORFOLOGIK_RULE_'),
                rule_id.startswith('SPELLING_RULE_'),
                rule_id.startswith('TYPOS'),
                rule_id.startswith('НЕВЕРНОЕ_'),
                rule_id.startswith('ПРОПУЩЕННОЕ_'),
                rule_id.startswith('НЕПРАВИЛЬНОЕ'),
                'СПЕЛЛЕР' in rule_id,
                'ОРФОГРАФИЯ' in rule_id,
                'ОПЕЧАТКА' in rule_id,
            ])

            # Проверка описания правила
            spelling_keywords = [
                'орфограф', 'правопис', 'опечатк', 'возможн', 'ошибк',
                'непра', 'проверьте', 'спеллер', 'писать', 'пишется'
            ]
            if not is_spelling_error and rule_desc:
                is_spelling_error = any(keyword in rule_desc for keyword in spelling_keywords)

            # Содержит ли сообщение об ошибке ключевые слова
            error_message = match.message.lower() if hasattr(match, 'message') else ""
            if not is_spelling_error and error_message:
                is_spelling_error = any(keyword in error_message for keyword in spelling_keywords)

            # Если это похоже на орфографическую ошибку, добавляем
            if is_spelling_error:
                error_data = {
                    'word': error_text,
                    'offset': match.offset,
                    'length': match.errorLength,
                    'message': getattr(match, 'message', "Возможная орфографическая ошибка"),
                    'replacements': getattr(match, 'replacements', []),
                    'rule_id': rule_id,
                    'found_by': 'languagetool'
                }

                if hasattr(match, 'ruleDescription'):
                    error_data['rule_description'] = match.ruleDescription
                elif hasattr(match, 'rule') and 'description' in match.rule:
                    error_data['rule_description'] = match.rule['description']

                spelling_errors.append(error_data)

        # 2. Дополнительная эвристическая проверка для выявления пропущенных ошибок
        # Особенно полезно для слов вроде "стоости"
        russian_vowels = 'аеёиоуыэюя'

        for word in words:
            # Пропускаем короткие слова и слова с цифрами
            if len(word) < 4 or any(c.isdigit() for c in word):
                continue

            # Пропускаем слова, которые уже помечены как ошибки
            already_marked = False
            for error in spelling_errors:
                if error['word'].lower() == word.lower():
                    already_marked = True
                    break

            if already_marked:
                continue

            # Эвристики для выявления типичных ошибок

            # 1. Три согласные подряд (кроме известных сочетаний)
            consonant_groups = re.findall(r'[бвгджзйклмнпрстфхцчшщ]{3,}', word.lower())
            valid_triples = ['вст', 'стр', 'нтр', 'ств', 'вск', 'нск', 'рск', 'стн']
            has_invalid_consonants = any(
                not any(triple in group.lower() for triple in valid_triples)
                for group in consonant_groups
            )

            # 2. Три гласные подряд
            vowel_groups = re.findall(f'[{russian_vowels}]{{3,}}', word.lower())

            # 3. Необычные повторения буквы (кроме известных случаев)
            repetitions = re.findall(r'(.)\1{2,}', word.lower())  # три и более одинаковых буквы подряд
            allowed_doubles = ['с', 'н', 'ж', 'з', 'к', 'т', 'м', 'в', 'л', 'п', 'р']
            unusual_doubles = re.findall(r'([^' + ''.join(allowed_doubles) + '])\1', word.lower())

            is_suspect = (
                    has_invalid_consonants or
                    vowel_groups or
                    repetitions or
                    unusual_doubles
            )

            # Если слово подозрительное, добавляем его как возможную ошибку
            if is_suspect:
                # Находим позицию этого слова в тексте
                positions = word_positions.get(word, [])
                if positions:
                    for pos in positions:
                        # Проверяем, не пересекается ли с уже найденными ошибками
                        overlapping = False
                        for error in spelling_errors:
                            error_start = error['offset']
                            error_end = error_start + error['length']
                            if pos >= error_start and pos < error_end:
                                overlapping = True
                                break

                        if not overlapping:
                            error_data = {
                                'word': word,
                                'offset': pos,
                                'length': len(word),
                                'message': "Возможная орфографическая ошибка",
                                'replacements': [],  # У нас нет предложений для замены
                                'rule_id': "CUSTOM_HEURISTIC_CHECK",
                                'rule_description': "Дополнительная эвристическая проверка",
                                'found_by': 'heuristic'
                            }
                            spelling_errors.append(error_data)

        # Сортируем ошибки по позиции в тексте
        spelling_errors.sort(key=lambda x: x['offset'])

        return spelling_errors
    except Exception as e:
        logging.error(f"Ошибка при проверке орфографии: {e}")
        return []

        return spelling_errors
    except Exception as e:
        logging.error(f"Ошибка при проверке орфографии: {e}")
        return []


def highlight_spelling_errors_in_html(text: str, errors: List[Dict]) -> str:
    """
    Добавляет HTML-разметку для подсветки слов с орфографическими ошибками.
    """
    if not errors:
        return text

    # Сортируем ошибки в обратном порядке, чтобы не сбивались индексы
    for error in sorted(errors, key=lambda x: x['offset'], reverse=True):
        start = error['offset']
        end = start + error['length']
        error_word = text[start:end]

        # Формируем подсказку с вариантами замены
        replacements_text = ", ".join(error["replacements"][:3]) if error["replacements"] else "нет вариантов"

        highlighted = (
            f'<span class="spelling-error" style="background-color: #ffcccc;" title="'
            f'Ошибка: {error["message"]}. '
            f'Исправления: {replacements_text}">'
            f'{error_word}</span>'
        )
        text = text[:start] + highlighted + text[end:]

    return text


def format_spelling_errors_list(errors: List[Dict]) -> str:
    """
    Формирует HTML-список с найденными орфографическими ошибками.
    """
    if not errors:
        return "<p>Орфографических ошибок не обнаружено.</p>"

    result = '<div class="spelling-list">'
    for i, error in enumerate(errors, 1):
        replacements = ", ".join(error["replacements"][:3]) if error["replacements"] else "нет вариантов"

        result += f'''
        <div class="spelling-item">
            <span class="spelling-word">{error['word']}</span>: {error['message']}
            <br>Варианты: {replacements}
        </div>
        '''
    result += '</div>'
    return result


# Добавляем тестовую функцию для проверки работы исправленного кода
def test_spell_checker(text=None):
    """
    Тестирует работу проверки орфографии на примере.
    Позволяет быстро оценить эффективность обнаружения ошибок.
    """
    if text is None:
        text = """
        Пример текста с разными ошибками:
        1. Выращийся цветок - морфологическая ошибка
        2. Стоости продукта - пропущенная буква
        3. Превед медвед - намеренное искажение
        4. Генирал армии - типичная ошибка в безударной гласной
        5. Руский язык - пропущенная буква в часто используемом слове
        6. Аппарат - правильное слово с удвоенной согласной
        7. Расчёт - правильное слово, где легко ошибиться
        """

    tool = init_spell_checker()
    errors = check_spelling_errors(text, tool)

    print(f"Найдено {len(errors)} ошибок:")
    for i, error in enumerate(errors, 1):
        print(f"{i}. {error['word']} - {error['message']}")
        if 'found_by' in error:
            print(f"   Обнаружено: {error['found_by']}")
        if error['replacements']:
            print(f"   Варианты замены: {', '.join(error['replacements'][:3])}")
        print()

    # Также выводим HTML-разметку
    html_output = highlight_spelling_errors_in_html(text, errors)
    print("\nHTML с подсветкой ошибок:")
    print(html_output)

    return errors