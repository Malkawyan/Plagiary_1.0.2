import os
import fitz
from langdetect import detect
from docx import Document
import pymupdf
import win32com.client
from striprtf.striprtf import rtf_to_text
from sentence_transformers import SentenceTransformer
import spacy
from transformers import AutoTokenizer
import numpy as np
from typing import List, Tuple, Optional

# Глобальные переменные для моделей (загружаются по требованию)
_model = None
_nlp_ru = None
_tokenizer = None

# Константы (добавьте ваши значения)
MAX_TOKENS = 512  # Пример значения, замените на нужное
BASE_FOLDER = "output"  # Папка для сохранения результатов
DATA_FOLDER = "data"  # Папка с исходными файлами


def get_model():
    """Получить модель SentenceTransformer (загружается при первом вызове)"""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer('paraphrase-xlm-r-multilingual-v1')
    return _model


def get_nlp():
    """Получить spaCy модель (загружается при первом вызове)"""
    global _nlp_ru
    if _nlp_ru is None:
        import spacy
        _nlp_ru = spacy.load("ru_core_news_lg")
    return _nlp_ru


def get_tokenizer():
    """Получить токенайзер (загружается при первом вызове)"""
    global _tokenizer
    if _tokenizer is None:
        from transformers import AutoTokenizer
        _tokenizer = AutoTokenizer.from_pretrained('sentence-transformers/paraphrase-xlm-r-multilingual-v1')
    return _tokenizer


def split_text_into_chunks(text: str, language: str) -> List[str]:
    """Разбивает текст на чанки с учетом максимального количества токенов."""
    nlp = get_nlp()
    tokenizer = get_tokenizer()
    doc = nlp(text)
    chunks = []
    current_chunk = []
    current_token_count = 0

    for sent in doc.sents:
        sent_text = sent.text.strip()
        if not sent_text:
            continue

        sent_tokens = tokenizer.tokenize(sent_text)
        sent_token_count = len(sent_tokens)

        if current_token_count + sent_token_count > MAX_TOKENS:
            if current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
                current_token_count = 0

            if sent_token_count > MAX_TOKENS:
                words = sent_text.split()
                sub_chunk = []
                sub_token_count = 0

                for word in words:
                    word_tokens = tokenizer.tokenize(word)
                    word_token_count = len(word_tokens)

                    if sub_token_count + word_token_count > MAX_TOKENS:
                        chunks.append(" ".join(sub_chunk))
                        sub_chunk = []
                        sub_token_count = 0

                    sub_chunk.append(word)
                    sub_token_count += word_token_count

                if sub_chunk:
                    chunks.append(" ".join(sub_chunk))
            else:
                current_chunk.append(sent_text)
                current_token_count = sent_token_count
        else:
            current_chunk.append(sent_text)
            current_token_count += sent_token_count

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


def preprocess_text_to_embeddings(text: str, language: str) -> List[np.ndarray]:
    """Обрабатывает текст любого размера, разбивая на части при необходимости."""
    model = get_model()
    nlp_ru = get_nlp()

    chunks = split_text_into_chunks(text, language)
    all_embeddings = []

    for chunk in chunks:
        sentences = [sent.text.strip() for sent in nlp_ru(chunk).sents if sent.text.strip()]
        if sentences:
            embeddings = model.encode(sentences)
            all_embeddings.extend(embeddings)

    return all_embeddings


def save_embeddings_to_file(embeddings: List[np.ndarray], file_path: str):
    """Сохраняет эмбеддинги в файл с информацией о количестве частей."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        for embedding in embeddings:
            f.write(' '.join(map(str, embedding)) + '\n')


def process_docx_file(file_path: str) -> Tuple[List[np.ndarray], int]:
    """Обработка .docx файлов с поддержкой больших текстов."""
    doc = Document(file_path)
    text = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
    language = detect(text[:500])  # Определяем язык по началу текста
    embeddings = preprocess_text_to_embeddings(text, language)
    return embeddings, len(embeddings)


def process_doc_file(file_path: str) -> Tuple[List[np.ndarray], int]:
    """Обработка .doc файлов с поддержкой больших текстов."""
    try:
        word = win32com.client.Dispatch("Word.Application")
        doc = word.Documents.Open(file_path)
        text = doc.Range().Text
        doc.Close()
        word.Quit()

        language = detect(text[:500])
        embeddings = preprocess_text_to_embeddings(text, language)
        return embeddings, len(embeddings)
    except Exception as e:
        print(f"Ошибка при обработке .doc файла: {e}")
        return [], 0


def process_pdf_file(file_path: str) -> Tuple[List[np.ndarray], int]:
    """Обработка .pdf файлов с поддержкой больших текстов."""
    try:
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text("text") + "\n"

        language = detect(text[:500])
        embeddings = preprocess_text_to_embeddings(text, language)
        return embeddings, len(embeddings)
    except Exception as e:
        print(f"Ошибка при обработке .pdf файла: {e}")
        return [], 0


def process_rtf_file(file_path: str) -> Tuple[List[np.ndarray], int]:
    """Обработка .rtf файлов с поддержкой больших текстов."""
    try:
        encodings = ['utf-8', 'windows-1251', 'cp1252', 'iso-8859-1']
        text = None

        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as file:
                    rtf_content = file.read()
                    text = rtf_to_text(rtf_content)
                    break
            except UnicodeDecodeError:
                continue

        if not text or not text.strip():
            print("RTF-файл не содержит текста или не может быть декодирован")
            return [], 0

        language = detect(text[:500])
        embeddings = preprocess_text_to_embeddings(text, language)
        return embeddings, len(embeddings)
    except Exception as e:
        print(f"Ошибка при обработке RTF-файла: {e}")
        return [], 0


def process_files_in_folder(folder_path: str):
    """Обрабатывает все файлы в папке с поддержкой больших текстов."""
    supported_extensions = ['.docx', '.doc', '.pdf', '.rtf']

    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)
        file_ext = os.path.splitext(file_name)[1].lower()

        if file_ext not in supported_extensions:
            continue

        output_path = os.path.join(BASE_FOLDER, f"{os.path.splitext(file_name)[0]}.txt")

        if os.path.exists(output_path):
            continue

        try:
            if file_ext == '.docx':
                embeddings, count = process_docx_file(file_path)
            elif file_ext == '.doc':
                embeddings, count = process_doc_file(file_path)
            elif file_ext == '.pdf':
                embeddings, count = process_pdf_file(file_path)
            elif file_ext == '.rtf':
                embeddings, count = process_rtf_file(file_path)

            if count > 0:
                save_embeddings_to_file(embeddings, output_path)
                print(f"Обработано: {file_name} | Предложений: {count} | Сохранено в: {output_path}")
            else:
                print(f"Файл {file_name} не содержит текста для обработки")

        except Exception as e:
            print(f"Ошибка при обработке {file_name}: {e}")


if __name__ == '__main__':
    process_files_in_folder(DATA_FOLDER)