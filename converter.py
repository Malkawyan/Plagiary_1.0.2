import os
import sys
import time
import logging
import json
import shutil
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QCheckBox, QScrollArea,
                             QLabel, QStyle, QMessageBox, QProgressDialog,
                             QDialog, QSlider, QGroupBox)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont

# Import processing functions from base.py
from base import process_docx_file, save_embeddings_to_file, BASE_FOLDER

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('converter_log.txt', mode='a')
    ]
)

# Пути к папкам
UPLOADS_DIR = 'uploads'
BACKUP_DIR = 'backup'
CONFIG_FILE = 'app/utils/config.json'
SIMILARITY_FILE = 'app/utils/similarity.py'

# Создаем папки, если они не существуют
for directory in [UPLOADS_DIR, BACKUP_DIR, '../app/utils']:
    if not os.path.exists(directory):
        os.makedirs(directory)
        logging.info(f"Создана папка {directory}")

# Значения по умолчанию
DEFAULT_THRESHOLD = 60


# Функция загрузки настроек
def load_settings():
    """Загружает настройки из конфигурационного файла"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Ошибка при загрузке настроек: {e}")

    # Возвращаем значения по умолчанию, если файл не существует или произошла ошибка
    return {"threshold": DEFAULT_THRESHOLD}


# Функция сохранения настроек
def save_settings(settings):
    """Сохраняет настройки в конфигурационный файл"""
    try:
        # Убедимся, что директория существует
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)

        with open(CONFIG_FILE, 'w') as f:
            json.dump(settings, f)
        logging.info(f"Настройки сохранены: {settings}")
        return True
    except Exception as e:
        logging.error(f"Ошибка при сохранении настроек: {e}")
        return False


# Функция обновления файла similarity.py
def update_similarity_threshold(threshold):
    """Обновляет значение порога в файле similarity.py"""
    try:
        # Проверяем существует ли файл
        if os.path.exists(SIMILARITY_FILE):
            with open(SIMILARITY_FILE, 'r', encoding='utf-8') as f:
                content = f.read()

            # Ищем строку с параметром threshold в функции calculate_uniqueness_and_similarity
            import re
            pattern = r'def calculate_uniqueness_and_similarity\(.*?threshold=(\d+)'
            match = re.search(pattern, content, re.DOTALL)

            if match:
                # Если нашли, заменяем значение
                current_threshold = match.group(1)
                new_content = content.replace(
                    f"def calculate_uniqueness_and_similarity(uploaded_embeddings, base_embeddings, sentences, threshold={current_threshold}",
                    f"def calculate_uniqueness_and_similarity(uploaded_embeddings, base_embeddings, sentences, threshold={threshold}"
                )

                with open(SIMILARITY_FILE, 'w', encoding='utf-8') as f:
                    f.write(new_content)

                logging.info(
                    f"Порог обновлен в файле similarity.py: threshold изменен с {current_threshold} на {threshold}")
            else:
                logging.warning("Не удалось найти параметр threshold в файле similarity.py")
                return False
        else:
            # Создаем файл, если он не существует
            directory = os.path.dirname(SIMILARITY_FILE)
            if not os.path.exists(directory):
                os.makedirs(directory)

            # Копируем содержимое из текущего файла similarity.py и обновляем порог
            with open('similarity.py', 'r', encoding='utf-8') as source:
                content = source.read()

            # Ищем строку с параметром threshold в функции calculate_uniqueness_and_similarity
            import re
            pattern = r'def calculate_uniqueness_and_similarity\(.*?threshold=(\d+)'
            match = re.search(pattern, content, re.DOTALL)

            if match:
                # Если нашли, заменяем значение
                current_threshold = match.group(1)
                new_content = content.replace(
                    f"def calculate_uniqueness_and_similarity(uploaded_embeddings, base_embeddings, sentences, threshold={current_threshold}",
                    f"def calculate_uniqueness_and_similarity(uploaded_embeddings, base_embeddings, sentences, threshold={threshold}"
                )

                with open(SIMILARITY_FILE, 'w', encoding='utf-8') as f:
                    f.write(new_content)

                logging.info(f"Создан файл similarity.py с порогом: threshold={threshold}")
            else:
                logging.warning("Не удалось найти параметр threshold в исходном файле similarity.py")
                # Копируем файл как есть, если не смогли найти параметр threshold
                shutil.copy2('similarity.py', SIMILARITY_FILE)
                logging.info("Файл similarity.py скопирован без изменений")

        return True
    except Exception as e:
        logging.error(f"Ошибка при обновлении порога в файле similarity.py: {e}", exc_info=True)
        return False


# Функция для отображения диалога настроек
def show_settings_dialog(main_window):
    """Отображает диалог настроек с ползунком для порога"""
    settings = load_settings()

    # Создаем диалог
    dialog = QDialog(main_window)
    dialog.setWindowTitle("Настройки")
    dialog.setMinimumWidth(400)

    # Основной макет
    layout = QVBoxLayout()

    # Группа настроек порога схожести
    threshold_group = QGroupBox("Настройки порога схожести")
    threshold_layout = QVBoxLayout()

    # Информация о пороге
    info_label = QLabel("Порог схожости определяет, при каком проценте схожести "
                        "предложение считается неуникальным. Меньшее значение делает "
                        "поиск более строгим и увеличивает количество совпадений.")
    info_label.setWordWrap(True)
    threshold_layout.addWidget(info_label)

    # Слайдер и метка для порога
    slider_layout = QHBoxLayout()
    threshold_value_label = QLabel(f"Порог схожести: {settings['threshold']}%")
    threshold_slider = QSlider(Qt.Horizontal)
    threshold_slider.setMinimum(30)
    threshold_slider.setMaximum(90)
    threshold_slider.setValue(settings['threshold'])
    threshold_slider.setTickPosition(QSlider.TicksBelow)
    threshold_slider.setTickInterval(10)

    # Обновляем метку при изменении слайдера
    def update_threshold_label(value):
        threshold_value_label.setText(f"Порог схожести: {value}%")

    threshold_slider.valueChanged.connect(update_threshold_label)

    slider_layout.addWidget(threshold_value_label)
    slider_layout.addWidget(threshold_slider)
    threshold_layout.addLayout(slider_layout)

    threshold_group.setLayout(threshold_layout)
    layout.addWidget(threshold_group)

    # Кнопки сохранения и отмены
    buttons_layout = QHBoxLayout()
    cancel_button = QPushButton("Отмена")
    save_button = QPushButton("Сохранить")

    cancel_button.clicked.connect(dialog.reject)

    def save_threshold():
        value = threshold_slider.value()
        settings['threshold'] = value
        save_settings(settings)
        update_similarity_threshold(value)
        dialog.accept()

    save_button.clicked.connect(save_threshold)

    buttons_layout.addWidget(cancel_button)
    buttons_layout.addWidget(save_button)
    layout.addLayout(buttons_layout)

    dialog.setLayout(layout)
    dialog.exec_()


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
    widget.checkbox = checkbox  # сохраняем ссылку на чекбокс для удобства
    widget.filename = filename  # сохраняем имя файла

    return widget


def load_files(file_list_layout, process_button, select_all_button, deselect_all_button, statusbar):
    """Загружает все .docx файлы из папки uploads и отображает их"""
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
        # Добавляем файлы в список
        for filename in docx_files:
            item = create_file_item(filename)
            file_list_layout.addWidget(item)

        # Добавляем растяжку, чтобы все элементы были вверху
        file_list_layout.addStretch()

        process_button.setEnabled(True)
        select_all_button.setEnabled(True)
        deselect_all_button.setEnabled(True)

    statusbar.showMessage('Готово')
    logging.info("Загрузка файлов завершена")


def select_all_files(file_list_layout, statusbar):
    """Выбрать все файлы в списке"""
    for i in range(file_list_layout.count()):
        widget = file_list_layout.itemAt(i).widget()
        if hasattr(widget, 'checkbox'):
            widget.checkbox.setChecked(True)

    statusbar.showMessage('Выбраны все файлы')


def deselect_all_files(file_list_layout, statusbar):
    """Снять выбор со всех файлов в списке"""
    for i in range(file_list_layout.count()):
        widget = file_list_layout.itemAt(i).widget()
        if hasattr(widget, 'checkbox'):
            widget.checkbox.setChecked(False)

    statusbar.showMessage('Выбор всех файлов отменен')


def process_selected_files(file_list_layout, statusbar, main_window):
    """Обработать выбранные файлы и конвертировать их в эмбеддинги"""
    selected_files = []

    # Получаем выбранные файлы
    for i in range(file_list_layout.count()):
        widget = file_list_layout.itemAt(i).widget()
        if hasattr(widget, 'checkbox') and widget.checkbox.isChecked():
            selected_files.append(widget.filename)

    if not selected_files:
        statusbar.showMessage('Нет выбранных файлов')
        logging.warning("Попытка обработки: нет выбранных файлов")
        return

    logging.info(f"Начало обработки {len(selected_files)} файлов")
    statusbar.showMessage(f'Начата обработка {len(selected_files)} файлов')

    # Создаем диалог прогресса
    progress = QProgressDialog("Обработка файлов...", "Отмена", 0, len(selected_files), main_window)
    progress.setWindowTitle("Прогресс обработки")
    progress.setWindowModality(Qt.WindowModal)
    progress.show()
    QApplication.processEvents()

    # Создаем папки base и backup, если они не существуют
    if not os.path.exists(BASE_FOLDER):
        os.makedirs(BASE_FOLDER)
        logging.info(f"Создана папка {BASE_FOLDER}")

    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
        logging.info(f"Создана папка {BACKUP_DIR}")

    # Обрабатываем каждый выбранный файл
    processed_count = 0
    skipped_count = 0
    processed_details = []

    for index, filename in enumerate(selected_files):
        # Обновляем прогресс
        progress.setValue(index)
        progress.setLabelText(f"Обработка файла: {filename}")
        QApplication.processEvents()

        if progress.wasCanceled():
            logging.warning("Обработка отменена пользователем")
            break

        file_path = os.path.join(UPLOADS_DIR, filename)
        output_filename = f"{os.path.splitext(filename)[0]}.txt"
        output_path = os.path.join(BASE_FOLDER, output_filename)

        # Проверяем, существует ли уже файл в папке base
        if os.path.exists(output_path):
            skipped_count += 1
            skip_message = f'Файл {filename} уже обработан (существует {output_filename})'
            processed_details.append(skip_message)
            statusbar.showMessage(skip_message)
            logging.info(skip_message)
            continue

        logging.info(f"Обработка файла {index + 1}/{len(selected_files)}: {filename}")

        try:
            start_time = time.time()

            # Обрабатываем файл с помощью функций из base.py
            logging.info(f"Начало обработки файла: {filename}")
            embeddings, count = process_docx_file(file_path)

            if count > 0:
                # Сохраняем эмбеддинги
                save_embeddings_to_file(embeddings, output_path)

                # Копируем файл в backup перед удалением
                backup_path = os.path.join(BACKUP_DIR, filename)
                shutil.copy2(file_path, backup_path)
                logging.info(f"Файл скопирован в резервную копию: {backup_path}")

                # Удаляем обработанный файл из uploads
                os.remove(file_path)
                processed_count += 1

                elapsed_time = time.time() - start_time
                status_message = f'Обработано: {filename} | Предложений: {count} | Время: {elapsed_time:.2f} сек.'
                processed_details.append(status_message)
                statusbar.showMessage(status_message)
                logging.info(status_message)
            else:
                error_message = f'Файл {filename} не содержит текста для обработки'
                processed_details.append(error_message)
                statusbar.showMessage(error_message)
                logging.warning(error_message)
        except Exception as e:
            error_message = f'Ошибка при обработке {filename}: {str(e)}'
            processed_details.append(error_message)
            statusbar.showMessage(error_message)
            logging.error(error_message, exc_info=True)

        # Немного задержки, чтобы позволить GUI обновиться
        QApplication.processEvents()

    # Закрываем диалог прогресса
    progress.setValue(len(selected_files))

    # Обновляем список файлов
    logging.info("Обновление списка файлов после обработки")
    load_files(file_list_layout, process_button, select_all_button, deselect_all_button, statusbar)

    # Показываем информационное окно о завершении обработки
    msg_box = QMessageBox(main_window)
    msg_box.setWindowTitle("Результат обработки")
    msg_box.setIcon(QMessageBox.Information)

    summary_text = f"Обработано файлов: {processed_count} из {len(selected_files)}\n"
    summary_text += f"Пропущено (уже обработаны): {skipped_count}\n\nДетали обработки:"
    for detail in processed_details:
        summary_text += f"\n• {detail}"

    msg_box.setText(summary_text)
    msg_box.setStandardButtons(QMessageBox.Ok)

    logging.info(f"Завершена обработка. Успешно: {processed_count}/{len(selected_files)}, пропущено: {skipped_count}")
    statusbar.showMessage(f'Обработано: {processed_count}, пропущено: {skipped_count}')
    msg_box.exec_()


# Основная часть программы
if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Устанавливаем стиль приложения
    app.setStyle('Fusion')

    # Создаем главное окно
    main_window = QMainWindow()
    main_window.setWindowTitle('Document Converter')
    main_window.setGeometry(100, 100, 800, 500)

    # Основной виджет и компоновка
    central_widget = QWidget()
    main_layout = QVBoxLayout(central_widget)

    # Заголовок
    title_label = QLabel("Конвертер документов в эмбеддинги")
    title_label.setFont(QFont('Arial', 14, QFont.Bold))
    title_label.setAlignment(Qt.AlignCenter)
    main_layout.addWidget(title_label)

    # Область контента
    content_layout = QHBoxLayout()

    # Область списка файлов
    file_area = QWidget()
    file_layout = QVBoxLayout(file_area)

    # Метка списка файлов
    file_list_label = QLabel("Файлы в папке uploads (только .docx):")
    file_list_label.setFont(QFont('Arial', 10, QFont.Bold))
    file_layout.addWidget(file_list_label)

    # Контейнер списка файлов с прокруткой
    file_list_container = QWidget()
    file_list_layout = QVBoxLayout(file_list_container)
    file_list_layout.setAlignment(Qt.AlignTop)
    file_list_layout.setSpacing(2)

    # Область с прокруткой для файлов
    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)
    scroll_area.setWidget(file_list_container)
    file_layout.addWidget(scroll_area)

    # Компоновка кнопок внизу
    buttons_layout = QHBoxLayout()

    # Кнопка "Обработать"
    process_button = QPushButton("Загрузить")
    process_button.setMinimumHeight(40)

    # Кнопка "Выбрать все"
    select_all_button = QPushButton("Выбрать все")

    # Кнопка "Снять выбор"
    deselect_all_button = QPushButton("Убрать все")

    # Добавляем кнопки в компоновку
    buttons_layout.addWidget(select_all_button)
    buttons_layout.addWidget(deselect_all_button)

    # Добавляем компоновку кнопок в компоновку файлов
    file_layout.addLayout(buttons_layout)
    file_layout.addWidget(process_button)

    # Добавляем область файлов в компоновку содержимого
    content_layout.addWidget(file_area, 4)  # 80% ширины

    # Область настроек (правая сторона)
    settings_area = QWidget()
    settings_layout = QVBoxLayout(settings_area)

    # Кнопка настроек (значок шестеренки)
    settings_button = QPushButton()
    settings_button.setIcon(main_window.style().standardIcon(QStyle.SP_FileDialogDetailedView))
    settings_button.setIconSize(QSize(32, 32))
    settings_button.setFixedSize(50, 50)
    settings_button.setToolTip("Настройки")

    # Привязываем действие к кнопке настроек
    settings_button.clicked.connect(lambda: show_settings_dialog(main_window))

    settings_layout.addWidget(settings_button, 0, Qt.AlignTop | Qt.AlignRight)
    settings_layout.addStretch()

    # Добавляем область настроек в компоновку содержимого
    content_layout.addWidget(settings_area, 1)  # 20% ширины

    # Добавляем компоновку содержимого в основную компоновку
    main_layout.addLayout(content_layout)

    # Устанавливаем центральный виджет
    main_window.setCentralWidget(central_widget)

    # Строка состояния
    statusbar = main_window.statusBar()
    statusbar.showMessage('Готово')

    # Подключаем функции к кнопкам
    select_all_button.clicked.connect(lambda: select_all_files(file_list_layout, statusbar))
    deselect_all_button.clicked.connect(lambda: deselect_all_files(file_list_layout, statusbar))
    process_button.clicked.connect(lambda: process_selected_files(file_list_layout, statusbar, main_window))

    # Загружаем файлы
    load_files(file_list_layout, process_button, select_all_button, deselect_all_button, statusbar)

    # Проверяем и создаем файл similarity.py, если он не существует
    if not os.path.exists(SIMILARITY_FILE):
        update_similarity_threshold(DEFAULT_THRESHOLD)

    # Показываем основное окно
    main_window.show()

    sys.exit(app.exec_())