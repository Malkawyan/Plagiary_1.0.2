import os
import shutil
import logging
from PyQt5 import Qt
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QCheckBox, QLabel


def create_file_item(filename):
    """Создает виджет для отображения файла с чекбоксом"""
    widget = QWidget()
    layout = QHBoxLayout()
    layout.setContentsMargins(5, 2, 5, 2)

    checkbox = QCheckBox()
    label = QLabel(filename)

    layout.addWidget(checkbox)
    layout.addWidget(label)
    layout.addStretch()

    widget.setLayout(layout)
    widget.checkbox = checkbox
    widget.filename = filename

    return widget


def load_files(file_list_layout, process_button, select_all_button, deselect_all_button, statusbar):
    """Загружает все .docx файлы из папки uploads и отображает их"""
    from settings import UPLOADS_DIR

    # Очищаем существующие элементы
    for i in reversed(range(file_list_layout.count())):
        widget = file_list_layout.itemAt(i).widget()
        if widget:
            widget.deleteLater()

    # Создаем папку uploads, если она не существует
    if not os.path.exists(UPLOADS_DIR):
        os.makedirs(UPLOADS_DIR)

    # Получаем все .docx файлы
    docx_files = [f for f in os.listdir(UPLOADS_DIR) if f.endswith('.docx')]
    logging.info(f"Найдено файлов .docx: {len(docx_files)}")

    if not docx_files:
        empty_label = QLabel("Нет файлов .docx в папке uploads")
        empty_label.setAlignment(Qt.AlignCenter)
        file_list_layout.addWidget(empty_label)
        process_button.setEnabled(False)
        select_all_button.setEnabled(False)
        deselect_all_button.setEnabled(False)
    else:
        for filename in docx_files:
            item = create_file_item(filename)
            file_list_layout.addWidget(item)

        file_list_layout.addStretch()
        process_button.setEnabled(True)
        select_all_button.setEnabled(True)
        deselect_all_button.setEnabled(True)

    statusbar.showMessage('Готово')
    logging.info("Загрузка файлов завершена")