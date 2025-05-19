import os
import sys
import shutil
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QCheckBox, QScrollArea,
                             QLabel, QFileSystemModel, QListView, QFrame, QStyle)
from PyQt5.QtCore import Qt, QDir, QModelIndex, QSize
from PyQt5.QtGui import QIcon, QFont

# Import processing functions from base.py
from base import process_docx_file, save_embeddings_to_file, BASE_FOLDER


class FileListItem(QWidget):
    """Custom widget for displaying file with checkbox"""

    def __init__(self, filename, parent=None):
        super().__init__(parent)
        self.filename = filename

        layout = QHBoxLayout()
        layout.setContentsMargins(5, 2, 5, 2)

        self.checkbox = QCheckBox()
        self.label = QLabel(filename)

        layout.addWidget(self.checkbox)
        layout.addWidget(self.label)
        layout.addStretch()

        self.setLayout(layout)


class DocConverterApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Document Converter')
        self.setGeometry(100, 100, 800, 500)

        # Main widget and layout
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)

        # Title label
        title_label = QLabel("Конвертер документов в эмбеддинги")
        title_label.setFont(QFont('Arial', 14, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        # Content area
        content_layout = QHBoxLayout()

        # File list area
        file_area = QWidget()
        file_layout = QVBoxLayout(file_area)

        # File list label
        file_list_label = QLabel("Файлы в папке uploads (только .docx):")
        file_list_label.setFont(QFont('Arial', 10, QFont.Bold))
        file_layout.addWidget(file_list_label)

        # File list container with scroll
        self.file_list_container = QWidget()
        self.file_list_layout = QVBoxLayout(self.file_list_container)
        self.file_list_layout.setAlignment(Qt.AlignTop)
        self.file_list_layout.setSpacing(2)

        # Scroll area for files
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.file_list_container)
        file_layout.addWidget(scroll_area)

        # Buttons layout at bottom
        buttons_layout = QHBoxLayout()

        # Process button
        self.process_button = QPushButton("Загрузить")
        self.process_button.setMinimumHeight(40)
        self.process_button.clicked.connect(self.process_selected_files)

        # Select all button
        self.select_all_button = QPushButton("Выбрать все")
        self.select_all_button.clicked.connect(self.select_all_files)

        # Deselect all button
        self.deselect_all_button = QPushButton("Убрать все")
        self.deselect_all_button.clicked.connect(self.deselect_all_files)

        # Add buttons to layout
        buttons_layout.addWidget(self.select_all_button)
        buttons_layout.addWidget(self.deselect_all_button)

        # Add buttons layout to file layout
        file_layout.addLayout(buttons_layout)
        file_layout.addWidget(self.process_button)

        # Add file area to content layout
        content_layout.addWidget(file_area, 4)  # 80% of width

        # Settings area (right side)
        settings_area = QWidget()
        settings_layout = QVBoxLayout(settings_area)

        # Settings button (gear icon)
        self.settings_button = QPushButton()
        self.settings_button.setIcon(self.style().standardIcon(QStyle.SP_FileDialogDetailedView))
        self.settings_button.setIconSize(QSize(32, 32))
        self.settings_button.setFixedSize(50, 50)
        self.settings_button.setToolTip("Настройки")

        settings_layout.addWidget(self.settings_button, 0, Qt.AlignTop | Qt.AlignRight)
        settings_layout.addStretch()

        # Add settings area to content layout
        content_layout.addWidget(settings_area, 1)  # 20% of width

        # Add content layout to main layout
        main_layout.addLayout(content_layout)

        # Set central widget
        self.setCentralWidget(central_widget)

        # Status bar
        self.statusBar().showMessage('Готово')

        # Load files
        self.load_files()

    def load_files(self):
        """Load all .docx files from uploads folder and display them"""
        # Clear existing items
        for i in reversed(range(self.file_list_layout.count())):
            self.file_list_layout.itemAt(i).widget().deleteLater()

        # Create uploads folder if it doesn't exist
        uploads_dir = 'uploads'
        if not os.path.exists(uploads_dir):
            os.makedirs(uploads_dir)

        # Get all .docx files
        docx_files = [f for f in os.listdir(uploads_dir) if f.endswith('.docx')]

        if not docx_files:
            empty_label = QLabel("Нет файлов .docx в папке uploads")
            empty_label.setAlignment(Qt.AlignCenter)
            self.file_list_layout.addWidget(empty_label)
            self.process_button.setEnabled(False)
            self.select_all_button.setEnabled(False)
            self.deselect_all_button.setEnabled(False)
        else:
            # Add files to list
            for filename in docx_files:
                item = FileListItem(filename)
                self.file_list_layout.addWidget(item)

            # Add a stretch to push all items to the top
            self.file_list_layout.addStretch()

            self.process_button.setEnabled(True)
            self.select_all_button.setEnabled(True)
            self.deselect_all_button.setEnabled(True)

    def select_all_files(self):
        """Select all files in the list"""
        for i in range(self.file_list_layout.count()):
            widget = self.file_list_layout.itemAt(i).widget()
            if isinstance(widget, FileListItem):
                widget.checkbox.setChecked(True)

        self.statusBar().showMessage('Выбраны все файлы')

    def deselect_all_files(self):
        """Deselect all files in the list"""
        for i in range(self.file_list_layout.count()):
            widget = self.file_list_layout.itemAt(i).widget()
            if isinstance(widget, FileListItem):
                widget.checkbox.setChecked(False)

        self.statusBar().showMessage('Выбор всех файлов отменен')

    def process_selected_files(self):
        """Process selected files and convert them to embeddings"""
        selected_files = []

        # Get selected files
        for i in range(self.file_list_layout.count()):
            widget = self.file_list_layout.itemAt(i).widget()
            if isinstance(widget, FileListItem) and widget.checkbox.isChecked():
                selected_files.append(widget.filename)

        if not selected_files:
            self.statusBar().showMessage('Нет выбранных файлов')
            return

        # Create base folder if it doesn't exist
        if not os.path.exists(BASE_FOLDER):
            os.makedirs(BASE_FOLDER)

        # Process each selected file
        processed_count = 0
        for filename in selected_files:
            file_path = os.path.join('uploads', filename)

            try:
                # Process the file using the base.py functions
                embeddings, count = process_docx_file(file_path)

                if count > 0:
                    # Save embeddings
                    output_path = os.path.join(BASE_FOLDER, f"{os.path.splitext(filename)[0]}.txt")
                    save_embeddings_to_file(embeddings, output_path)

                    # Remove the processed file from uploads
                    os.remove(file_path)
                    processed_count += 1

                    self.statusBar().showMessage(f'Обработано: {filename} | Предложений: {count}')
                else:
                    self.statusBar().showMessage(f'Файл {filename} не содержит текста для обработки')
            except Exception as e:
                self.statusBar().showMessage(f'Ошибка при обработке {filename}: {str(e)}')

        # Refresh file list
        self.load_files()

        self.statusBar().showMessage(f'Обработано файлов: {processed_count}')


if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Set app style
    app.setStyle('Fusion')

    # Create and show the main window
    main_window = DocConverterApp()
    main_window.show()

    sys.exit(app.exec_())