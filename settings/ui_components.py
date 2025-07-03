import os
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QScrollArea, QLabel, QStyle,
                             QDialog, QSlider, QGroupBox, QMessageBox,
                             QFrame, QSizePolicy, QCheckBox)
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

    # Увеличенные шрифты для презентации
    TITLE_FONT = QFont('Segoe UI', 24, QFont.Bold)
    HEADER_FONT = QFont('Segoe UI', 18, QFont.Bold)
    NORMAL_FONT = QFont('Segoe UI', 16)
    BUTTON_FONT = QFont('Segoe UI', 16, QFont.Bold)
    SUBTITLE_FONT = QFont('Segoe UI', 14)

    @staticmethod
    def setup_button(button, primary=True, icon=None, large=False):
        """Стилизуем кнопку в соответствии с цветовой схемой"""
        padding = "12px 24px" if large else "10px 20px"

        if primary:
            button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {StyleHelper.PRIMARY_COLOR};
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: {padding};
                    min-height: 20px;
                }}
                QPushButton:hover {{
                    background-color: {StyleHelper.ACCENT_COLOR};
                }}
                QPushButton:pressed {{
                    background-color: {StyleHelper.ACCENT_COLOR};
                }}
                QPushButton:disabled {{
                    background-color: #CCCCCC;
                    color: #666666;
                }}
            """)
        else:
            button.setStyleSheet(f"""
                QPushButton {{
                    background-color: white;
                    color: {StyleHelper.PRIMARY_COLOR};
                    border: 2px solid {StyleHelper.SECONDARY_COLOR};
                    border-radius: 8px;
                    padding: {padding};
                    min-height: 20px;
                }}
                QPushButton:hover {{
                    background-color: {StyleHelper.BG_COLOR};
                    border-color: {StyleHelper.PRIMARY_COLOR};
                }}
                QPushButton:pressed {{
                    background-color: {StyleHelper.LIGHT_COLOR};
                }}
                QPushButton:disabled {{
                    background-color: #F5F5F5;
                    color: #CCCCCC;
                    border-color: #CCCCCC;
                }}
            """)

        button.setFont(StyleHelper.BUTTON_FONT)
        if icon:
            button.setIcon(icon)
            button.setIconSize(QSize(24, 24))  # Увеличенные иконки

    @staticmethod
    def create_separator():
        """Создает горизонтальную разделительную линию"""
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setMinimumHeight(2)
        line.setStyleSheet(f"background-color: {StyleHelper.LIGHT_COLOR};")
        return line

    @staticmethod
    def style_groupbox(groupbox):
        """Стилизует GroupBox"""
        groupbox.setStyleSheet(f"""
            QGroupBox {{
                border: 2px solid {StyleHelper.LIGHT_COLOR};
                border-radius: 10px;
                margin-top: 20px;
                padding-top: 15px;
                font-weight: bold;
                color: {StyleHelper.TEXT_COLOR};
                font-size: 16px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 10px;
                color: {StyleHelper.PRIMARY_COLOR};
                font-size: 18px;
                font-weight: bold;
            }}
        """)

    @staticmethod
    def style_checkbox(checkbox):
        """Стилизует чекбокс для лучшей видимости"""
        checkbox.setStyleSheet(f"""
            QCheckBox {{
                font-size: 16px;
                color: {StyleHelper.TEXT_COLOR};
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 20px;
                height: 20px;
                border: 2px solid {StyleHelper.SECONDARY_COLOR};
                border-radius: 4px;
                background-color: white;
            }}
            QCheckBox::indicator:checked {{
                background-color: {StyleHelper.PRIMARY_COLOR};
                border-color: {StyleHelper.PRIMARY_COLOR};
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIHZpZXdCb3g9IjAgMCAxNiAxNiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEzLjM1NCA0LjM1NEwxNC42NDY5IDUuNjQ2OUw2IDEzLjI5MzhMMSAyMS4yOTM4TDIuMjkyIDEuMDAwMkw2IDcuNzA3MTFMMTMuMzU0IDQuMzU0WiIgZmlsbD0id2hpdGUiLz4KPHN2Zz4K);
            }}
        """)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Конвертер документов для университета')

        self.setGeometry(50, 50, 1400, 900)
        self.setMinimumSize(1200, 800)

        # Установка стиля окна
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{
                background-color: white;
                color: {StyleHelper.TEXT_COLOR};
            }}
            QScrollArea {{
                border: 2px solid {StyleHelper.LIGHT_COLOR};
                border-radius: 8px;
                background-color: white;
            }}
            QLabel {{
                color: {StyleHelper.TEXT_COLOR};
            }}
            QStatusBar {{
                background-color: {StyleHelper.BG_COLOR};
                color: {StyleHelper.TEXT_COLOR};
                border-top: 2px solid {StyleHelper.LIGHT_COLOR};
                font-size: 14px;
                padding: 8px;
            }}
            QSlider::groove:horizontal {{
                border: 2px solid {StyleHelper.LIGHT_COLOR};
                height: 12px;
                background: white;
                margin: 4px 0;
                border-radius: 6px;
            }}
            QSlider::handle:horizontal {{
                background: {StyleHelper.PRIMARY_COLOR};
                border: 2px solid {StyleHelper.PRIMARY_COLOR};
                width: 24px;
                margin: -4px 0;
                border-radius: 12px;
            }}
            QSlider::sub-page:horizontal {{
                background: {StyleHelper.SECONDARY_COLOR};
                border-radius: 6px;
            }}
        """)

        self.central_widget = QWidget()
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(30, 30, 30, 30)
        self.main_layout.setSpacing(25)

        self._setup_ui()
        self.setCentralWidget(self.central_widget)

        self.statusbar = self.statusBar()
        self.statusbar.showMessage('Готово к работе')

    def _setup_ui(self):
        # Заголовок с логотипом и информацией
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 20)

        title_widget = QWidget()
        title_layout = QVBoxLayout(title_widget)
        title_layout.setContentsMargins(0, 0, 0, 0)

        title_label = QLabel("Конвертер документов в эмбеддинги")
        title_label.setFont(StyleHelper.TITLE_FONT)
        title_label.setStyleSheet(f"color: {StyleHelper.PRIMARY_COLOR};")

        subtitle_label = QLabel("Кафедра информационных технологий")
        subtitle_label.setFont(StyleHelper.SUBTITLE_FONT)
        subtitle_label.setStyleSheet(f"color: {StyleHelper.SECONDARY_COLOR};")

        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)

        header_layout.addWidget(title_widget)
        header_layout.addStretch()

        # Кнопка настроек в шапке
        self.settings_button = QPushButton("⚙️ Настройки")
        self.settings_button.setFixedSize(180, 60)
        self.settings_button.setToolTip("Настройки порога схожести")
        StyleHelper.setup_button(self.settings_button, primary=False, large=True)
        self.settings_button.clicked.connect(self._show_settings_dialog)

        header_layout.addWidget(self.settings_button)

        self.main_layout.addWidget(header_widget)
        self.main_layout.addWidget(StyleHelper.create_separator())

        # Основная область контента
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 15, 0, 0)
        content_layout.setSpacing(30)

        # ---- Левая панель: список файлов ----
        file_panel = QWidget()
        file_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        file_panel_layout = QVBoxLayout(file_panel)
        file_panel_layout.setContentsMargins(0, 0, 0, 0)
        file_panel_layout.setSpacing(15)

        file_header = QWidget()
        file_header_layout = QHBoxLayout(file_header)
        file_header_layout.setContentsMargins(0, 0, 0, 10)

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
            border-radius: 10px;
            padding: 20px;
        """)
        files_layout = QVBoxLayout(files_container)

        self.file_list_container = QWidget()
        self.file_list_layout = QVBoxLayout(self.file_list_container)
        self.file_list_layout.setAlignment(Qt.AlignTop)
        self.file_list_layout.setSpacing(8)
        self.file_list_layout.setContentsMargins(10, 10, 10, 10)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.file_list_container)
        scroll_area.setMinimumHeight(300)
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
        buttons_layout.setContentsMargins(0, 10, 0, 10)
        buttons_layout.setSpacing(15)

        self.select_all_button = QPushButton("✓ Выбрать все")
        self.deselect_all_button = QPushButton("✗ Убрать все")
        self.add_file_button = QPushButton("📁 Добавить файл")
        self.process_button = QPushButton("🚀 ЗАГРУЗИТЬ")

        # Устанавливаем размеры кнопок
        button_height = 50
        self.select_all_button.setMinimumHeight(button_height)
        self.deselect_all_button.setMinimumHeight(button_height)
        self.add_file_button.setMinimumHeight(button_height)
        self.process_button.setMinimumHeight(button_height)
        self.process_button.setMinimumWidth(200)

        StyleHelper.setup_button(self.select_all_button, primary=False, large=True)
        StyleHelper.setup_button(self.deselect_all_button, primary=False, large=True)
        StyleHelper.setup_button(self.add_file_button, primary=False, large=True)
        StyleHelper.setup_button(self.process_button, primary=True, large=True)

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
        info_panel.setMaximumWidth(400)
        info_panel_layout = QVBoxLayout(info_panel)
        info_panel_layout.setContentsMargins(0, 0, 0, 0)
        info_panel_layout.setSpacing(20)

        info_box = QGroupBox("ℹ️ Информация")
        StyleHelper.style_groupbox(info_box)
        info_box_layout = QVBoxLayout(info_box)
        info_box_layout.setSpacing(15)

        info_text = QLabel(
            "Данный инструмент позволяет конвертировать документы Word (.docx) "
            "в эмбеддинги для дальнейшего анализа текста.\n\n"
            "📋 Выберите файлы из списка\n"
            "🚀 Нажмите кнопку 'ЗАГРУЗИТЬ'"
        )
        info_text.setWordWrap(True)
        info_text.setFont(StyleHelper.NORMAL_FONT)
        info_box_layout.addWidget(info_text)

        help_text = QLabel(
            "💡 Советы:\n"
            "• Используйте 'Добавить файл' для новых документов\n"
            "• Настройте порог схожести в настройках\n"
            "• Обработанные файлы сохраняются в папке base"
        )
        help_text.setWordWrap(True)
        help_text.setFont(StyleHelper.NORMAL_FONT)
        info_box_layout.addWidget(help_text)

        info_panel_layout.addWidget(info_box)

        # Статус обработки
        status_box = QGroupBox("📊 Статус обработки")
        StyleHelper.style_groupbox(status_box)
        status_box_layout = QVBoxLayout(status_box)

        self.status_label = QLabel("⏳ Ожидание выбора файлов")
        self.status_label.setWordWrap(True)
        self.status_label.setFont(StyleHelper.NORMAL_FONT)
        self.status_label.setMinimumHeight(60)
        self.status_label.setStyleSheet(f"""
            QLabel {{
                padding: 15px;
                background-color: {StyleHelper.BG_COLOR};
                border-radius: 8px;
                border: 1px solid {StyleHelper.LIGHT_COLOR};
            }}
        """)
        status_box_layout.addWidget(self.status_label)

        info_panel_layout.addWidget(status_box)
        info_panel_layout.addStretch()

        content_layout.addWidget(info_panel)

        self.main_layout.addWidget(content_widget, 1)

        # Подключение сигналов
        self.select_all_button.clicked.connect(self._select_all_files)
        self.deselect_all_button.clicked.connect(self._deselect_all_files)
        self.add_file_button.clicked.connect(self._add_external_file)
        self.process_button.clicked.connect(self._process_files)

    def _select_all_files(self):
        for i in range(self.file_list_layout.count()):
            widget = self.file_list_layout.itemAt(i).widget()
            if hasattr(widget, 'checkbox'):
                widget.checkbox.setChecked(True)
        self.statusbar.showMessage('✅ Выбраны все файлы')
        self.status_label.setText('✅ Выбраны все файлы')

    def _deselect_all_files(self):
        for i in range(self.file_list_layout.count()):
            widget = self.file_list_layout.itemAt(i).widget()
            if hasattr(widget, 'checkbox'):
                widget.checkbox.setChecked(False)
        self.statusbar.showMessage('❌ Выбор всех файлов отменен')
        self.status_label.setText('❌ Выбор файлов отменен')

    def _add_external_file(self):
        """Вызывает функцию добавления внешнего файла"""
        self.status_label.setText('📁 Добавление файла...')
        success = add_external_file(self)
        if success:
            self.status_label.setText('✅ Файл успешно добавлен')
        else:
            self.status_label.setText('⏳ Ожидание выбора файлов')

    def _process_files(self):
        """Запускает обработку выбранных файлов"""
        self.process_button.setEnabled(False)
        self.process_button.setText("⏳ ОБРАБОТКА...")

        self.status_label.setText('🔄 Обработка файлов...')

        try:
            def restore_button():
                self.process_button.setEnabled(True)
                self.process_button.setText("🚀 ЗАГРУЗИТЬ")

            self._restore_button = restore_button
            process_selected_files(self.file_list_layout, self.statusbar, self)

        except Exception as e:
            import logging
            logging.error(f"Ошибка при обработке файлов: {e}")
            self.status_label.setText('❌ Ошибка при обработке файлов')
            self.statusbar.showMessage('❌ Ошибка при обработке файлов')
            self.process_button.setEnabled(True)
            self.process_button.setText("🚀 ЗАГРУЗИТЬ")

    def _show_settings_dialog(self):
        settings = load_settings()

        dialog = QDialog(self)
        dialog.setWindowTitle("Настройки")
        dialog.setMinimumSize(600, 400)
        dialog.setStyleSheet(f"""
            QDialog {{
                background-color: white;
                color: {StyleHelper.TEXT_COLOR};
            }}
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Заголовок диалога
        title_label = QLabel("⚙️ Настройки параметров")
        title_label.setFont(StyleHelper.HEADER_FONT)
        title_label.setStyleSheet(f"color: {StyleHelper.PRIMARY_COLOR};")
        layout.addWidget(title_label)
        layout.addWidget(StyleHelper.create_separator())

        # Группа настроек порога схожести
        threshold_group = QGroupBox("🎯 Настройки порога схожести")
        StyleHelper.style_groupbox(threshold_group)
        threshold_layout = QVBoxLayout()
        threshold_layout.setSpacing(15)

        info_label = QLabel(
            "Порог схожести определяет, при каком проценте схожести "
            "предложение считается неуникальным.\n\n"
            "• Рекомендуемое значение: 60-70%"
        )
        info_label.setWordWrap(True)
        info_label.setFont(StyleHelper.NORMAL_FONT)
        threshold_layout.addWidget(info_label)

        slider_widget = QWidget()
        slider_layout = QVBoxLayout(slider_widget)

        self.threshold_value_label = QLabel(f"📊 Текущий порог: {settings['threshold']}%")
        self.threshold_value_label.setFont(StyleHelper.HEADER_FONT)
        self.threshold_value_label.setStyleSheet(f"color: {StyleHelper.PRIMARY_COLOR};")
        self.threshold_value_label.setAlignment(Qt.AlignCenter)

        threshold_slider = QSlider(Qt.Horizontal)
        threshold_slider.setMinimum(30)
        threshold_slider.setMaximum(90)
        threshold_slider.setValue(settings['threshold'])
        threshold_slider.setTickPosition(QSlider.TicksBelow)
        threshold_slider.setTickInterval(10)
        threshold_slider.setMinimumHeight(40)

        # Подписи к слайдеру
        slider_labels = QWidget()
        labels_layout = QHBoxLayout(slider_labels)
        labels_layout.setContentsMargins(0, 0, 0, 0)

        threshold_slider.valueChanged.connect(
            lambda value: self.threshold_value_label.setText(f"📊 Текущий порог: {value}%"))

        slider_layout.addWidget(self.threshold_value_label)
        slider_layout.addWidget(threshold_slider)
        slider_layout.addWidget(slider_labels)

        threshold_layout.addWidget(slider_widget)

        threshold_group.setLayout(threshold_layout)
        layout.addWidget(threshold_group)
        layout.addStretch()

        # Кнопки действий
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(15)

        cancel_button = QPushButton("❌ Отмена")
        save_button = QPushButton("💾 Сохранить")

        cancel_button.setMinimumHeight(50)
        save_button.setMinimumHeight(50)
        save_button.setMinimumWidth(150)

        StyleHelper.setup_button(cancel_button, primary=False, large=True)
        StyleHelper.setup_button(save_button, primary=True, large=True)

        cancel_button.clicked.connect(dialog.reject)

        def save_threshold():
            value = threshold_slider.value()
            settings['threshold'] = value
            save_settings(settings)
            update_similarity_threshold(value)
            self.statusbar.showMessage(f'✅ Порог схожести изменен на {value}%')
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
        # Добавляем эмодзи к сообщениям для лучшей визуализации
        if "ошибка" in message.lower():
            message = f"❌ {message}"
        elif "завершен" in message.lower() or "готов" in message.lower():
            message = f"✅ {message}"
        elif "обработка" in message.lower():
            message = f"🔄 {message}"
        elif "ожидан" in message.lower():
            message = f"⏳ {message}"

        self.status_label.setText(message)