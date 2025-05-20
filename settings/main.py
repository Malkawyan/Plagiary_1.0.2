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

    # Проверяем и создаем файл similarity.py, если он не существует
    if not main_window.similarity_file_exists():
        update_similarity_threshold(DEFAULT_THRESHOLD)

    main_window.show()
    sys.exit(app.exec_())