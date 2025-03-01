import numpy as np
from app.utils.embeddings import preprocess_text_to_embeddings, load_embeddings_from_file
from app.utils.similarity import calculate_similarity
from app.config import Config
from pathlib import Path

def process_text(text, language):
    uploaded_embeddings = preprocess_text_to_embeddings(text, language)
    base_sentences = set()
    base_folder_path = Path(Config.BASE_FOLDER)

    if not base_folder_path.exists():
        raise FileNotFoundError("Base folder does not exist")

    for base_file in base_folder_path.iterdir():
        if base_file.is_file():
            base_embeddings = load_embeddings_from_file(base_file)
            for emb2 in base_embeddings:
                base_sentences.add(tuple(emb2))

    unique_sentences = 0
    total_sentences = len(uploaded_embeddings)

    for emb1 in uploaded_embeddings:
        emb_tuple = tuple(emb1)
        match_found = False

        for base_emb_tuple in base_sentences:
            similarity = calculate_similarity(emb1, np.array(base_emb_tuple))
            if similarity > 80:
                match_found = True
                break

        if not match_found:
            unique_sentences += 1

    unique_percentage = (unique_sentences / total_sentences) * 100 if total_sentences > 0 else 100
    return {"overall_uniqueness": f"{unique_percentage:.2f}%"}