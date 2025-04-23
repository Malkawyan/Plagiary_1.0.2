import numpy as np
from functools import lru_cache
from typing import List, Dict, Union
from .model_loader import model_loader

nlp = model_loader.nlp
tokenizer = model_loader.tokenizer
model = model_loader.model


def split_text_into_sentences(text: str) -> List[str]:
    """Разбивает текст на предложения с помощью NLP модели."""
    return [sent.text.strip() for sent in nlp(text).sents]


def split_text_into_chunks(text: str, max_tokens: int = 512) -> List[str]:
    """
    Разбивает текст на части, не превышающие max_tokens токенов.
    Сохраняет целостность предложений.
    """
    chunks = []
    current_chunk = []
    current_token_count = 0

    for sent in split_text_into_sentences(text):
        sent_tokens = tokenizer.tokenize(sent)
        sent_token_count = len(sent_tokens)

        if current_token_count + sent_token_count > max_tokens:
            if current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
                current_token_count = 0

            if sent_token_count > max_tokens:
                words = sent.split()
                sub_chunk = []
                sub_token_count = 0

                for word in words:
                    word_tokens = tokenizer.tokenize(word)
                    word_token_count = len(word_tokens)

                    if sub_token_count + word_token_count > max_tokens:
                        chunks.append(" ".join(sub_chunk))
                        sub_chunk = []
                        sub_token_count = 0

                    sub_chunk.append(word)
                    sub_token_count += word_token_count

                if sub_chunk:
                    chunks.append(" ".join(sub_chunk))
            else:
                current_chunk.append(sent)
                current_token_count = sent_token_count
        else:
            current_chunk.append(sent)
            current_token_count += sent_token_count

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks