import os
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QScrollArea, QLabel, QStyle,
                             QDialog, QSlider, QGroupBox, QMessageBox,
                             QFrame, QSizePolicy)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QPalette, QColor, QIcon, QPixmap
from settings import load_settings, save_settings, update_similarity_threshold
from file_operations import load_files, add_external_file
from processing import process_selected_files


class StyleHelper:
    # Цветовая палитра в сине-голубых тонах
    PRIMARY_COLOR = "#2C5F96"  # Основной синий
    SECONDARY_COLOR = "#6CA6C1"  # Голубой
    ACCENT_COLOR = "#0B3C5D"  # Темно-синий
    LIGHT_COLOR = "#A9D6E5"  # Светло-голубой
    BG_COLOR = "#F5F9FC"  # Фоновый светлый
    TEXT_COLOR = "#1E3A5F"  # Цвет текста
    SUCCESS_COLOR = "#2E7D32"  # Зеленый для успешных действий

    TITLE_FONT = QFont('Segoe UI', 14, QFont.Bold)
    HEADER_FONT = QFont('Segoe UI', 11, QFont.Bold)
    NORMAL_FONT = QFont('Segoe UI', 10)
    BUTTON_FONT = QFont('Segoe UI', 10)

    @staticmethod
    def setup_button(button, primary=True, icon=None):
        """Стилизует кнопку в соответствии с цветовой схемой"""
        if primary:
            button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {StyleHelper.PRIMARY_COLOR};
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 6px 12px;
                }}
                QPushButton:hover {{
                    background-color: {StyleHelper.ACCENT_COLOR};
                }}
                QPushButton:pressed {{
                    background-color: {StyleHelper.ACCENT_COLOR};
                }}
            """)
        else:
            button.setStyleSheet(f"""
                QPushButton {{
                    background-color: white;
                    color: {StyleHelper.PRIMARY_COLOR};
                    border: 1px solid {StyleHelper.SECONDARY_COLOR};
                    border-radius: 4px;
                    padding: 6px 12px;
                }}
                QPushButton:hover {{
                    background-color: {StyleHelper.BG_COLOR};
                }}
                QPushButton:pressed {{
                    background-color: {StyleHelper.LIGHT_COLOR};
                }}
            """)

        button.setFont(StyleHelper.BUTTON_FONT)
        if icon:
            button.setIcon(icon)

    @staticmethod
    def create_separator():
        """Создает горизонтальную разделительную линию"""
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet(f"background-color: {StyleHelper.LIGHT_COLOR};")
        return line

    @staticmethod
    def style_groupbox(groupbox):
        """Стилизует GroupBox"""
        groupbox.setStyleSheet(f"""
            QGroupBox {{
                border: 1px solid {StyleHelper.LIGHT_COLOR};
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 10px;
                font-weight: bold;
                color: {StyleHelper.TEXT_COLOR};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 6px;
                color: {StyleHelper.PRIMARY_COLOR};
            }}
        """)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Конвертер документов для университета')
        self.setGeometry(100, 100, 960, 600)

        # Установка стиля окна
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{
                background-color: white;
                color: {StyleHelper.TEXT_COLOR};
            }}
            QScrollArea {{
                border: 1px solid {StyleHelper.LIGHT_COLOR};
                border-radius: 4px;
                background-color: white;
            }}
            QLabel {{
                color: {StyleHelper.TEXT_COLOR};
            }}
            QStatusBar {{
                background-color: {StyleHelper.BG_COLOR};
                color: {StyleHelper.TEXT_COLOR};
                border-top: 1px solid {StyleHelper.LIGHT_COLOR};
            }}
            QSlider::groove:horizontal {{
                border: 1px solid {StyleHelper.LIGHT_COLOR};
                height: 8px;
                background: white;
                margin: 2px 0;
                border-radius: 4px;
            }}
            QSlider::handle:horizontal {{
                background: {StyleHelper.PRIMARY_COLOR};
                border: 1px solid {StyleHelper.PRIMARY_COLOR};
                width: 18px;
                margin: -2px 0;
                border-radius: 9px;
            }}
            QSlider::sub-page:horizontal {{
                background: {StyleHelper.SECONDARY_COLOR};
                border-radius: 4px;
            }}
        """)

        self.central_widget = QWidget()
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)

        self._setup_ui()
        self.setCentralWidget(self.central_widget)

        self.statusbar = self.statusBar()
        self.statusbar.showMessage('Готово')

    def _setup_ui(self):
        # Заголовок с логотипом и информацией
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 10)

        # Можно добавить логотип университета
        # logo_label = QLabel()
        # logo_label.setPixmap(QPixmap("logo.png").scaledToHeight(50, Qt.SmoothTransformation))
        # header_layout.addWidget(logo_label)

        title_widget = QWidget()
        title_layout = QVBoxLayout(title_widget)
        title_layout.setContentsMargins(0, 0, 0, 0)

        title_label = QLabel("Конвертер документов в эмбеддинги")
        title_label.setFont(StyleHelper.TITLE_FONT)
        title_label.setStyleSheet(f"color: {StyleHelper.PRIMARY_COLOR};")

        subtitle_label = QLabel("Кафедра информационных технологий")
        subtitle_label.setFont(QFont('Segoe UI', 10))
        subtitle_label.setStyleSheet(f"color: {StyleHelper.SECONDARY_COLOR};")

        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)

        header_layout.addWidget(title_widget)
        header_layout.addStretch()

        # Кнопка настроек в шапке с пользовательской иконкой
        self.settings_button = QPushButton()

        # Попытка загрузить пользовательскую иконку
        settings_icon = self._load_settings_icon()
        if settings_icon:
            self.settings_button.setIcon(settings_icon)
        else:
            # Если пользовательская иконка недоступна, используем стандартную
            self.settings_button.setIcon(self.style().standardIcon(QStyle.SP_FileDialogDetailedView))

        self.settings_button.setIconSize(QSize(24, 24))
        self.settings_button.setFixedSize(40, 40)
        self.settings_button.setToolTip("Настройки")
        StyleHelper.setup_button(self.settings_button, primary=False)
        self.settings_button.clicked.connect(self._show_settings_dialog)

        header_layout.addWidget(self.settings_button)

        self.main_layout.addWidget(header_widget)
        self.main_layout.addWidget(StyleHelper.create_separator())

        # Основная область контента
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 10, 0, 0)
        content_layout.setSpacing(20)

        # ---- Левая панель: список файлов ----
        file_panel = QWidget()
        file_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        file_panel_layout = QVBoxLayout(file_panel)
        file_panel_layout.setContentsMargins(0, 0, 0, 0)
        file_panel_layout.setSpacing(10)

        file_header = QWidget()
        file_header_layout = QHBoxLayout(file_header)
        file_header_layout.setContentsMargins(0, 0, 0, 0)

        file_list_label = QLabel("Файлы в папке uploads (только .docx):")
        file_list_label.setFont(StyleHelper.HEADER_FONT)
        file_list_label.setStyleSheet(f"color: {StyleHelper.PRIMARY_COLOR};")

        file_header_layout.addWidget(file_list_label)
        file_header_layout.addStretch()

        file_panel_layout.addWidget(file_header)

        # Контейнер для списка файлов
        files_container = QWidget()
        files_container.setStyleSheet(f"""
            background-color: {StyleHelper.BG_COLOR};
            border-radius: 6px;
            padding: 10px;
        """)
        files_layout = QVBoxLayout(files_container)

        self.file_list_container = QWidget()
        self.file_list_layout = QVBoxLayout(self.file_list_container)
        self.file_list_layout.setAlignment(Qt.AlignTop)
        self.file_list_layout.setSpacing(4)
        self.file_list_layout.setContentsMargins(5, 5, 5, 5)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.file_list_container)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)

        files_layout.addWidget(scroll_area)
        file_panel_layout.addWidget(files_container, 1)

        # Кнопки управления файлами
        buttons_widget = QWidget()
        buttons_layout = QHBoxLayout(buttons_widget)
        buttons_layout.setContentsMargins(0, 5, 0, 5)
        buttons_layout.setSpacing(10)

        self.select_all_button = QPushButton("Выбрать все")
        self.deselect_all_button = QPushButton("Убрать все")
        self.add_file_button = QPushButton("Добавить файл")
        self.process_button = QPushButton("Загрузить")

        # Добавляем иконку для кнопки добавления файла
        add_file_icon = self.style().standardIcon(QStyle.SP_DirOpenIcon)
        self.add_file_button.setIcon(add_file_icon)

        StyleHelper.setup_button(self.select_all_button, primary=False)
        StyleHelper.setup_button(self.deselect_all_button, primary=False)
        StyleHelper.setup_button(self.add_file_button, primary=False)
        StyleHelper.setup_button(self.process_button, primary=True)

        # Добавляем всплывающую подсказку
        self.add_file_button.setToolTip("Добавить .docx файл из проводника")

        buttons_layout.addWidget(self.select_all_button)
        buttons_layout.addWidget(self.deselect_all_button)
        buttons_layout.addWidget(self.add_file_button)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.process_button)

        file_panel_layout.addWidget(buttons_widget)
        content_layout.addWidget(file_panel, 1)

        # ---- Правая панель: статус и информация ----
        info_panel = QWidget()
        info_panel.setMaximumWidth(300)
        info_panel_layout = QVBoxLayout(info_panel)
        info_panel_layout.setContentsMargins(0, 0, 0, 0)
        info_panel_layout.setSpacing(15)

        info_box = QGroupBox("Информация")
        StyleHelper.style_groupbox(info_box)
        info_box_layout = QVBoxLayout(info_box)

        info_text = QLabel(
            "Данный инструмент позволяет конвертировать документы Word (.docx) "
            "в эмбеддинги для дальнейшего анализа текста. Выберите файлы из списка "
            "и нажмите кнопку 'Загрузить'."
        )
        info_text.setWordWrap(True)
        info_text.setFont(StyleHelper.NORMAL_FONT)
        info_box_layout.addWidget(info_text)

        help_text = QLabel(
            "Для добавления новых файлов используйте кнопку 'Добавить файл'. "
            "Для настройки порога схожести используйте кнопку настроек."
        )
        help_text.setWordWrap(True)
        help_text.setFont(StyleHelper.NORMAL_FONT)
        info_box_layout.addWidget(help_text)

        info_panel_layout.addWidget(info_box)

        # Статус обработки
        status_box = QGroupBox("Статус обработки")
        StyleHelper.style_groupbox(status_box)
        status_box_layout = QVBoxLayout(status_box)

        self.status_label = QLabel("Ожидание выбора файлов")
        self.status_label.setWordWrap(True)
        self.status_label.setFont(StyleHelper.NORMAL_FONT)
        status_box_layout.addWidget(self.status_label)

        info_panel_layout.addWidget(status_box)
        info_panel_layout.addStretch()

        content_layout.addWidget(info_panel)

        self.main_layout.addWidget(content_widget, 1)

        # Подключение сигналов
        self.select_all_button.clicked.connect(self._select_all_files)
        self.deselect_all_button.clicked.connect(self._deselect_all_files)
        self.add_file_button.clicked.connect(self._add_external_file)
        self.process_button.clicked.connect(lambda: self._process_files())

    def _load_settings_icon(self):
        """Загружает пользовательскую иконку настроек"""
        # Список возможных имен файлов иконки
        icon_names = ['settings.png', 'gear.png', 'config.png', 'настройки.png']

        for icon_name in icon_names:
            if os.path.exists(icon_name):
                try:
                    pixmap = QPixmap(icon_name)
                    if not pixmap.isNull():
                        # Масштабируем иконку до нужного размера с сохранением пропорций
                        scaled_pixmap = pixmap.scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        return QIcon(scaled_pixmap)
                except Exception as e:
                    print(f"Ошибка загрузки иконки {icon_name}: {e}")
                    continue

        # Если не удалось загрузить пользовательскую иконку
        print("Пользовательская иконка не найдена. Используется стандартная иконка.")
        return None

    def _select_all_files(self):
        for i in range(self.file_list_layout.count()):
            widget = self.file_list_layout.itemAt(i).widget()
            if hasattr(widget, 'checkbox'):
                widget.checkbox.setChecked(True)
        self.statusbar.showMessage('Выбраны все файлы')
        self.status_label.setText('Выбраны все файлы')

    def _deselect_all_files(self):
        for i in range(self.file_list_layout.count()):
            widget = self.file_list_layout.itemAt(i).widget()
            if hasattr(widget, 'checkbox'):
                widget.checkbox.setChecked(False)
        self.statusbar.showMessage('Выбор всех файлов отменен')
        self.status_label.setText('Выбор файлов отменен')

    def _add_external_file(self):
        """Вызывает функцию добавления внешнего файла"""
        self.status_label.setText('Добавление файла...')
        success = add_external_file(self)
        if success:
            self.status_label.setText('Файл успешно добавлен')
        else:
            self.status_label.setText('Ожидание выбора файлов')

    def _process_files(self):
        self.status_label.setText('Обработка файлов...')
        process_selected_files(self.file_list_layout, self.statusbar, self)
        self.status_label.setText('Обработка завершена')

    def _show_settings_dialog(self):
        settings = load_settings()

        dialog = QDialog(self)
        dialog.setWindowTitle("Настройки")
        dialog.setMinimumWidth(450)
        dialog.setStyleSheet(f"""
            QDialog {{
                background-color: white;
                color: {StyleHelper.TEXT_COLOR};
            }}
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Заголовок диалога
        title_label = QLabel("Настройки параметров")
        title_label.setFont(StyleHelper.HEADER_FONT)
        title_label.setStyleSheet(f"color: {StyleHelper.PRIMARY_COLOR};")
        layout.addWidget(title_label)
        layout.addWidget(StyleHelper.create_separator())

        # Группа настроек порога схожести
        threshold_group = QGroupBox("Настройки порога схожести")
        StyleHelper.style_groupbox(threshold_group)
        threshold_layout = QVBoxLayout()

        info_label = QLabel("Порог схожести определяет, при каком проценте схожести "
                            "предложение считается неуникальным. Меньшее значение делает "
                            "поиск более строгим и увеличивает количество совпадений.")
        info_label.setWordWrap(True)
        info_label.setFont(StyleHelper.NORMAL_FONT)
        threshold_layout.addWidget(info_label)

        slider_layout = QHBoxLayout()
        self.threshold_value_label = QLabel(f"Порог схожести: {settings['threshold']}%")
        self.threshold_value_label.setFont(StyleHelper.NORMAL_FONT)
        self.threshold_value_label.setMinimumWidth(120)

        threshold_slider = QSlider(Qt.Horizontal)
        threshold_slider.setMinimum(30)
        threshold_slider.setMaximum(90)
        threshold_slider.setValue(settings['threshold'])
        threshold_slider.setTickPosition(QSlider.TicksBelow)
        threshold_slider.setTickInterval(10)

        threshold_slider.valueChanged.connect(
            lambda value: self.threshold_value_label.setText(f"Порог схожести: {value}%"))

        slider_layout.addWidget(self.threshold_value_label)
        slider_layout.addWidget(threshold_slider, 1)
        threshold_layout.addLayout(slider_layout)

        threshold_group.setLayout(threshold_layout)
        layout.addWidget(threshold_group)
        layout.addStretch()

        # Кнопки действий
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)

        cancel_button = QPushButton("Отмена")
        save_button = QPushButton("Сохранить")

        StyleHelper.setup_button(cancel_button, primary=False)
        StyleHelper.setup_button(save_button, primary=True)

        cancel_button.clicked.connect(dialog.reject)

        def save_threshold():
            value = threshold_slider.value()
            settings['threshold'] = value
            save_settings(settings)
            update_similarity_threshold(value)
            self.statusbar.showMessage(f'Порог схожести изменен на {value}%')
            dialog.accept()

        save_button.clicked.connect(save_threshold)

        buttons_layout.addStretch()
        buttons_layout.addWidget(cancel_button)
        buttons_layout.addWidget(save_button)
        layout.addLayout(buttons_layout)

        dialog.setLayout(layout)
        dialog.exec_()

    def similarity_file_exists(self):
        from settings import SIMILARITY_FILE
        return os.path.exists(SIMILARITY_FILE)

    def update_status(self, message):
        """Обновляет текст статуса в панели информации"""
        self.status_label.setText(message)