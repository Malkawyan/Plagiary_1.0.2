import sys
from PyQt5.QtWidgets import QApplication
from ui_components import MainWindow
from file_operations import load_files
from settings import update_similarity_threshold, DEFAULT_THRESHOLD

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    main_window = MainWindow()

    # Загружаем файлы при старте
    load_files(
        main_window.file_list_layout,
        main_window.process_button,
        main_window.select_all_button,
        main_window.deselect_all_button,
        main_window.statusbar
    )

    # Проверяем файл similarity.py
    if not main_window.similarity_file_exists():
        update_similarity_threshold(DEFAULT_THRESHOLD)

    # Показываем окно сразу
    main_window.show()

    # Опционально: предварительная загрузка моделей в фоне
    from PyQt5.QtCore import QTimer


    def preload_models():
        try:
            # Импортируем и инициализируем модели в фоне
            from base import get_model, get_nlp
            get_model()  # Загружаем модель
            get_nlp()  # Загружаем spaCy
            main_window.statusbar.showMessage('✅ Модели загружены')
        except Exception as e:
            main_window.statusbar.showMessage(f'⚠️ Ошибка загрузки моделей: {e}')


    # Загружаем модели через 1 секунду после показа интерфейса
    QTimer.singleShot(1000, preload_models)

    sys.exit(app.exec_())