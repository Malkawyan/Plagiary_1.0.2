import os
import shutil
import logging
from PyQt5 import Qt
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QCheckBox, QLabel, QFileDialog, QMessageBox


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


def add_external_file(main_window):
    """Открывает диалог выбора файла и копирует выбранный .docx файл в папку uploads"""
    from settings import UPLOADS_DIR

    try:
        # Создаем папку uploads, если она не существует
        if not os.path.exists(UPLOADS_DIR):
            os.makedirs(UPLOADS_DIR)
            logging.info(f"Создана папка {UPLOADS_DIR}")

        # Открываем диалог выбора файла
        file_path, _ = QFileDialog.getOpenFileName(
            main_window,
            "Выберите файл .docx",
            "",
            "Документы Word (*.docx);;Все файлы (*)"
        )

        if not file_path:
            # Пользователь отменил выбор
            return False

        # Получаем имя файла
        filename = os.path.basename(file_path)
        destination_path = os.path.join(UPLOADS_DIR, filename)

        # Проверяем, существует ли уже такой файл
        if os.path.exists(destination_path):
            reply = QMessageBox.question(
                main_window,
                "Файл уже существует",
                f"Файл '{filename}' уже существует в папке uploads.\n"
                "Хотите заменить его?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply != QMessageBox.Yes:
                main_window.statusbar.showMessage("Добавление файла отменено")
                return False

        # Копируем файл в папку uploads
        shutil.copy2(file_path, destination_path)

        # Логируем успешное добавление
        logging.info(f"Файл {filename} успешно добавлен в {UPLOADS_DIR}")
        main_window.statusbar.showMessage(f"Файл '{filename}' успешно добавлен")

        # Обновляем список файлов
        load_files(
            main_window.file_list_layout,
            main_window.process_button,
            main_window.select_all_button,
            main_window.deselect_all_button,
            main_window.statusbar
        )

        return True

    except Exception as e:
        error_msg = f"Ошибка при добавлении файла: {str(e)}"
        logging.error(error_msg, exc_info=True)

        QMessageBox.critical(
            main_window,
            "Ошибка",
            f"Не удалось добавить файл:\n{str(e)}"
        )

        main_window.statusbar.showMessage("Ошибка при добавлении файла")
        return False


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