from language_tool_python import LanguageTool
from typing import List, Dict, Union
import logging
import time

logging.basicConfig(level=logging.INFO)
logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)


def init_spell_checker(language='ru-RU'):
    """Инициализируем LanguageTool с увеличенным лимитом"""
    try:
        tool = LanguageTool(language, config={'maxTextLength': 50000})
    except:
        tool = LanguageTool(language)

    # Отключаем лишние правила
    for rule in ['PUNCTUATION', 'TYPOGRAPHY', 'CASING']:
        try:
            tool.disable(rule)
        except:
            pass
    return tool


def split_text(text: str, chunk_size: int = 8000) -> List[Dict]:
    """Режем текст на куски"""
    if len(text) <= chunk_size:
        return [{'text': text, 'offset': 0}]

    chunks = []
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))

        # Ищем конец предложения
        if end < len(text):
            for punct in ['.', '!', '?']:
                pos = text.rfind(punct, start, end)
                if pos > start + chunk_size // 2:
                    end = pos + 1
                    break

        chunks.append({'text': text[start:end], 'offset': start})
        start = end

    return chunks


def check_spelling_errors(text: str, tool: LanguageTool) -> List[Dict[str, Union[str, int]]]:
    """Проверяем орфографию с поддержкой больших файлов"""
    chunks = split_text(text)
    all_errors = []

    for i, chunk in enumerate(chunks):
        print(f"Обрабатываю кусок {i + 1}/{len(chunks)}")

        # Повторяем до 3 раз при сетевых ошибках
        for attempt in range(3):
            try:
                matches = tool.check(chunk['text'])
                break
            except Exception as e:
                if "Connection aborted" in str(e) and attempt < 2:
                    time.sleep(1)
                    continue
                matches = []
                break

        # Обрабатываем найденные ошибки
        for match in matches:
            rule_id = match.ruleId
            if any(x in rule_id.upper() for x in ['SPELL', 'TYPO', 'MORFOLOGIK', 'GRAMMAR']):
                error_offset = chunk['offset'] + match.offset
                error_text = text[error_offset:error_offset + match.errorLength]

                # Пропускаем короткие слова
                if len(error_text.strip()) > 2:
                    all_errors.append({
                        'word': error_text,
                        'offset': error_offset,
                        'length': match.errorLength,
                        'message': getattr(match, 'message', "Орфографическая ошибка"),
                        'replacements': getattr(match, 'replacements', [])
                    })

        time.sleep(0.1)  # Не перегружаем сервер

    # Убираем дубликаты и сортируем
    unique_errors = list({(e['offset'], e['word']): e for e in all_errors}.values())
    return sorted(unique_errors, key=lambda x: x['offset'])


def highlight_spelling_errors_in_html(text: str, errors: List[Dict]) -> str:
    """Оборачиваем ошибки в HTML"""
    if not errors:
        return text

    result = text
    for error in sorted(errors, key=lambda x: x['offset'], reverse=True):
        start = error['offset']
        end = start + error['length']
        word = result[start:end]

        replacements = ", ".join(error["replacements"][:3]) if error["replacements"] else "нет вариантов"
        highlight = f'<span style="background-color: #ffcccc;" title="{error["message"]}. Варианты: {replacements}">{word}</span>'

        result = result[:start] + highlight + result[end:]

    return result