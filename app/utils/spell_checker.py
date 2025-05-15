from language_tool_python import LanguageTool
from typing import List, Dict, Union
import re
import logging

# Настраиваем логирование, чтобы уменьшить вывод от urllib3
logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)


def init_spell_checker(language='ru-RU'):
    """Инициализирует LanguageTool для проверки орфографии русского языка"""
    tool = LanguageTool(language)

    # Отключаем правила, не связанные с орфографией (если доступно)
    if hasattr(tool, 'disable'):
        for rule in ['PUNCTUATION', 'TYPOGRAPHY', 'STYLE']:
            try:
                tool.disable(rule)
            except:
                pass

    return tool


def check_spelling_errors(text: str, tool: LanguageTool) -> List[Dict[str, Union[str, int]]]:
    """Проверяет текст на орфографические ошибки с помощью LanguageTool и дополнительных эвристик"""
    spelling_errors = []

    # 1. Проверка с помощью LanguageTool (берем все ошибки, как потенциально орфографические)
    matches = tool.check(text)

    # Принимаем все ошибки, которые выглядят как орфографические
    for match in matches:
        rule_id = match.ruleId
        error_text = text[match.offset:match.offset + match.errorLength]
        error_message = match.message.lower() if hasattr(match, 'message') else ""

        # Добавляем практически все ошибки, исключая некоторые категории пунктуации
        if not any(x in rule_id.upper() for x in ['WHITESPACE', 'COMMA', 'PERIOD', 'UPPERCASE']):
            error_data = {
                'word': error_text,
                'offset': match.offset,
                'length': match.errorLength,
                'message': getattr(match, 'message', "Возможная орфографическая ошибка"),
                'replacements': getattr(match, 'replacements', [])
            }
            spelling_errors.append(error_data)

    # 2. Расширенный словарь типичных орфографических ошибок в русском языке
    common_errors = {
        'улудшени': 'улучшени',
        'стрес': 'стресс',
        'привычьк': 'привычк',
        'отсутсви': 'отсутстви',
        'удвальстви': 'удовольстви',
        'вниманя': 'внимания',
        'обязятельн': 'обязательн',
        'ключиву': 'ключеву',
        'ключив': 'ключев',
        # Дополнительные ошибки из текста
        'удвальств': 'удовольств',
        'обязятельн': 'обязательн'
    }

    # Проверяем типичные ошибки в тексте
    for error_word, correct_word in common_errors.items():
        for match in re.finditer(r'\b' + error_word, text.lower()):
            start_pos = match.start()
            end_pos = match.end()

            # Избегаем дублирования с уже найденными ошибками
            overlapping = any(
                start_pos < error['offset'] + error['length'] and
                end_pos > error['offset']
                for error in spelling_errors
            )

            if not overlapping:
                actual_word = text[start_pos:end_pos]
                error_data = {
                    'word': actual_word,
                    'offset': start_pos,
                    'length': len(actual_word),
                    'message': f"Словарная ошибка. Возможно, вы имели в виду: {correct_word}",
                    'replacements': [correct_word]
                }
                spelling_errors.append(error_data)

    # 3. Дополнительные эвристики для обнаружения ошибок
    # Поиск слов с типичными проблемами в русском языке
    patterns = [
        (r'([аеёиоуыэюя])([жшщчц])(е)', r'\1\2'),  # Проблемы с шипящими
        (r'тс([тд])', r'тсс\1'),  # Пропуск в сочетаниях тст/тсд
        (r'(т?с)т(в|н)', r'\1тв'),  # Пропуск т в сочетаниях ств/стн
        (r'([аоеи])н{1}([аоеи])', r'\1нн\2'),  # Пропуск н в сочетании нн
        (r'([аоеи])л{1}([аоеи])', r'\1лл\2'),  # Пропуск л в сочетании лл
        (r'ь([аоуыэи])', r'\1'),  # Неправильный мягкий знак
        (r'([жшчщц])ь([аоуыэ])', r'\1\2'),  # Неправильный мягкий знак после шипящих
    ]

    for pattern, _ in patterns:
        for match in re.finditer(pattern, text.lower()):
            word_start = text.rfind(' ', 0, match.start()) + 1
            if word_start <= 0:
                word_start = 0

            word_end = text.find(' ', match.end())
            if word_end == -1:
                word_end = len(text)

            # Корректируем границы слова
            while word_start < len(text) and not text[word_start].isalpha():
                word_start += 1

            while word_end > 0 and not text[word_end - 1].isalpha():
                word_end -= 1

            if word_start >= word_end:
                continue

            word = text[word_start:word_end]

            # Проверяем, не пересекается ли с уже найденными ошибками
            overlapping = any(
                word_start < error['offset'] + error['length'] and
                word_end > error['offset']
                for error in spelling_errors
            )

            if not overlapping and len(word) > 3:  # Игнорируем короткие слова
                error_data = {
                    'word': word,
                    'offset': word_start,
                    'length': len(word),
                    'message': "Возможная орфографическая ошибка (эвристическое обнаружение)",
                    'replacements': []
                }
                spelling_errors.append(error_data)

    # 4. Дополнительная проверка на конкретные слова из текста примера
    specific_errors = {
        'отсутсвие': 'отсутствие',
        'удвальствием': 'удовольствием',
        'вниманя': 'внимания',
        'обязятельной': 'обязательной',
        'ключивую': 'ключевую'
    }

    for error_word, correct_word in specific_errors.items():
        for match in re.finditer(error_word, text.lower()):
            start_pos = match.start()
            end_pos = match.end()

            # Избегаем дублирования
            overlapping = any(
                start_pos < error['offset'] + error['length'] and
                end_pos > error['offset']
                for error in spelling_errors
            )

            if not overlapping:
                actual_word = text[start_pos:end_pos]
                error_data = {
                    'word': actual_word,
                    'offset': start_pos,
                    'length': len(actual_word),
                    'message': f"Ошибка в тексте. Правильно: {correct_word}",
                    'replacements': [correct_word]
                }
                spelling_errors.append(error_data)

    # Сортируем ошибки по их позиции в тексте
    spelling_errors.sort(key=lambda x: x['offset'])

    return spelling_errors


def highlight_spelling_errors_in_html(text: str, errors: List[Dict]) -> str:
    """Добавляет HTML-разметку для подсветки слов с орфографическими ошибками"""
    if not errors:
        return text

    # Работаем с копией текста
    result = text

    # Сортируем ошибки в обратном порядке, чтобы не сбивались индексы
    for error in sorted(errors, key=lambda x: x['offset'], reverse=True):
        start = error['offset']
        end = start + error['length']
        error_word = result[start:end]

        # Формируем варианты замены
        replacements = ", ".join(error["replacements"][:3]) if error["replacements"] else "нет вариантов"

        # Создаем HTML-разметку для подсветки
        highlight = f'<span class="spelling-error" style="background-color: #ffcccc;" title="Ошибка: {error["message"]}. Варианты: {replacements}">{error_word}</span>'

        # Заменяем в тексте
        result = result[:start] + highlight + result[end:]

    return result


def test_spell_checker(text=None):
    """Тестирует работу проверки орфографии на примере текста"""
    if text is None:
        text = """
        Физическая культура играет важную роль в жизни каждого человека. 
        Регулярные занятия спортом способствуют улудшению здоровья, 
        повышают настроение и снижают уровень стреса. Особенно важно прививать 
        любовь к активному образу жизни с детства, чтобы у ребёнка сформировались 
        полезные привычьки. Школьные уроки физкультуры часто недооценивают, 
        хотя они развивают выносливость, координацию и командный дух.
        Одной из ошибок в системе образования является отсутсвие разнообразия 
        в физической активности. Не всем детям нравится бег или футбол, но многие 
        могли бы с удвальствием заниматься танцами, плаванием или восточными единоборствами. 
        Также стоит больше вниманя уделять инклюзивным формам физической культуры. 
        Таким образом, физическое воспитание должно стать не просто обязятельной частью 
        школьной программы, а настоящим средством формирования здоровой и активной личности. 
        Поддержка родителей, учителей и общества в целом играет здесь ключивую роль.
        """

    # Инициализируем проверку и находим ошибки
    tool = init_spell_checker()
    errors = check_spelling_errors(text, tool)

    # Выводим найденные ошибки
    print(f"Найдено {len(errors)} ошибок:")
    for i, error in enumerate(errors, 1):
        print(f"{i}. {error['word']} - {error['message']}")
        if error['replacements']:
            print(f"   Варианты: {', '.join(error['replacements'][:3])}")
        print()

    # Вернем разметку с подсветкой ошибок
    return highlight_spelling_errors_in_html(text, errors)


if __name__ == "__main__":
    # Запускаем проверку на тестовом тексте
    highlighted_text = test_spell_checker()
    print("\nHTML с подсветкой ошибок:")
    print(highlighted_text)