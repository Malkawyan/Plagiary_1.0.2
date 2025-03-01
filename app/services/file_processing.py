from docx import Document
import PyPDF2
import logging

def read_file(file_path):
    """
    Универсальная функция для чтения файлов разных форматов (TXT, DOCX, PDF).

    :param file_path: Путь к файлу
    :return: Текст файла в виде строки
    """
    try:
        if file_path.endswith('.txt'):
            # Открываем и читаем содержимое TXT-файла
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        elif file_path.endswith('.docx'):
            # Извлекаем текст из DOCX-файла
            doc = Document(file_path)
            return '\n'.join([para.text for para in doc.paragraphs])
        elif file_path.endswith('.pdf'):
            # Извлекаем текст из PDF-файла
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ''
                for page in reader.pages:
                    text += page.extract_text()
                return text
        else:
            raise ValueError("Неподдерживаемый формат файла.")
    except Exception as e:
        logging.error(f"Ошибка чтения файла {file_path}: {e}")
        raise