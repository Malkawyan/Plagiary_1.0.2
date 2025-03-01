import os

class Config:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, '..', 'uploads')
    BASE_FOLDER = os.path.join(BASE_DIR, '..', 'base')
    BASE_WORDS_FOLDER = os.path.join(BASE_DIR, '..', 'base_words')
    STATIC_FOLDER = os.path.join(BASE_DIR, '..', 'app/static')
    APP_FOLDER = os.path.join(BASE_DIR, '..', 'app')

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(BASE_FOLDER, exist_ok=True)