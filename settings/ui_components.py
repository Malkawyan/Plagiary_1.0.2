import os
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QScrollArea, QLabel, QStyle,
                             QDialog, QSlider, QGroupBox, QMessageBox)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont
from settings import load_settings, save_settings, update_similarity_threshold
from file_operations import load_files
from processing import process_selected_files


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Document Converter')
        self.setGeometry(100, 100, 800, 500)

        self.central_widget = QWidget()
        self.main_layout = QVBoxLayout(self.central_widget)

        self._setup_ui()
        self.setCentralWidget(self.central_widget)

        self.statusbar = self.statusBar()
        self.statusbar.showMessage('Готово')

    def _setup_ui(self):
        # Заголовок
        title_label = QLabel("Конвертер документов в эмбеддинги")
        title_label.setFont(QFont('Arial', 14, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(title_label)

        # Область контента
        content_layout = QHBoxLayout()

        # Область списка файлов
        file_area = QWidget()
        self.file_layout = QVBoxLayout(file_area)

        file_list_label = QLabel("Файлы в папке uploads (только .docx):")
        file_list_label.setFont(QFont('Arial', 10, QFont.Bold))
        self.file_layout.addWidget(file_list_label)

        self.file_list_container = QWidget()
        self.file_list_layout = QVBoxLayout(self.file_list_container)
        self.file_list_layout.setAlignment(Qt.AlignTop)
        self.file_list_layout.setSpacing(2)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.file_list_container)
        self.file_layout.addWidget(scroll_area)

        buttons_layout = QHBoxLayout()

        self.process_button = QPushButton("Загрузить")
        self.process_button.setMinimumHeight(40)

        self.select_all_button = QPushButton("Выбрать все")
        self.deselect_all_button = QPushButton("Убрать все")

        buttons_layout.addWidget(self.select_all_button)
        buttons_layout.addWidget(self.deselect_all_button)

        self.file_layout.addLayout(buttons_layout)
        self.file_layout.addWidget(self.process_button)
        content_layout.addWidget(file_area, 4)

        # Область настроек
        settings_area = QWidget()
        settings_layout = QVBoxLayout(settings_area)

        self.settings_button = QPushButton()
        self.settings_button.setIcon(self.style().standardIcon(QStyle.SP_FileDialogDetailedView))
        self.settings_button.setIconSize(QSize(32, 32))
        self.settings_button.setFixedSize(50, 50)
        self.settings_button.setToolTip("Настройки")

        self.settings_button.clicked.connect(self._show_settings_dialog)
        settings_layout.addWidget(self.settings_button, 0, Qt.AlignTop | Qt.AlignRight)
        settings_layout.addStretch()

        content_layout.addWidget(settings_area, 1)
        self.main_layout.addLayout(content_layout)

        # Подключение сигналов
        self.select_all_button.clicked.connect(lambda: self._select_all_files())
        self.deselect_all_button.clicked.connect(lambda: self._deselect_all_files())
        self.process_button.clicked.connect(lambda: process_selected_files(
            self.file_list_layout, self.statusbar, self
        ))

    def _select_all_files(self):
        for i in range(self.file_list_layout.count()):
            widget = self.file_list_layout.itemAt(i).widget()
            if hasattr(widget, 'checkbox'):
                widget.checkbox.setChecked(True)
        self.statusbar.showMessage('Выбраны все файлы')

    def _deselect_all_files(self):
        for i in range(self.file_list_layout.count()):
            widget = self.file_list_layout.itemAt(i).widget()
            if hasattr(widget, 'checkbox'):
                widget.checkbox.setChecked(False)
        self.statusbar.showMessage('Выбор всех файлов отменен')

    def _show_settings_dialog(self):
        settings = load_settings()

        dialog = QDialog(self)
        dialog.setWindowTitle("Настройки")
        dialog.setMinimumWidth(400)

        layout = QVBoxLayout()

        threshold_group = QGroupBox("Настройки порога схожести")
        threshold_layout = QVBoxLayout()

        info_label = QLabel("Порог схожости определяет, при каком проценте схожести "
                            "предложение считается неуникальным. Меньшее значение делает "
                            "поиск более строгим и увеличивает количество совпадений.")
        info_label.setWordWrap(True)
        threshold_layout.addWidget(info_label)

        slider_layout = QHBoxLayout()
        self.threshold_value_label = QLabel(f"Порог схожести: {settings['threshold']}%")
        threshold_slider = QSlider(Qt.Horizontal)
        threshold_slider.setMinimum(30)
        threshold_slider.setMaximum(90)
        threshold_slider.setValue(settings['threshold'])
        threshold_slider.setTickPosition(QSlider.TicksBelow)
        threshold_slider.setTickInterval(10)

        threshold_slider.valueChanged.connect(
            lambda value: self.threshold_value_label.setText(f"Порог схожести: {value}%"))

        slider_layout.addWidget(self.threshold_value_label)
        slider_layout.addWidget(threshold_slider)
        threshold_layout.addLayout(slider_layout)

        threshold_group.setLayout(threshold_layout)
        layout.addWidget(threshold_group)

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

    def similarity_file_exists(self):
        from settings import SIMILARITY_FILE
        return os.path.exists(SIMILARITY_FILE)