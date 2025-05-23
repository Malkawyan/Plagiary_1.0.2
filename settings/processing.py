import os
import time
import logging
import shutil

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import QProgressDialog, QMessageBox
from base import process_docx_file, save_embeddings_to_file, BASE_FOLDER
from settings import UPLOADS_DIR, BACKUP_DIR


class FileProcessingThread(QThread):
    """Поток для обработки файлов в фоновом режиме"""

    # Сигналы для обновления UI
    progress_updated = pyqtSignal(int, str)  # прогресс, текущий файл
    file_processed = pyqtSignal(str, bool, str)  # имя файла, успех, сообщение
    processing_finished = pyqtSignal(int, int, int, list)  # обработано, всего, пропущено, детали

    def __init__(self, selected_files):
        super().__init__()
        self.selected_files = selected_files
        self.should_cancel = False

    def cancel(self):
        """Отменить обработку"""
        self.should_cancel = True

    def run(self):
        """Основной метод обработки файлов"""
        if not os.path.exists(BASE_FOLDER):
            os.makedirs(BASE_FOLDER)
            logging.info(f"Создана папка {BASE_FOLDER}")

        if not os.path.exists(BACKUP_DIR):
            os.makedirs(BACKUP_DIR)
            logging.info(f"Создана папка {BACKUP_DIR}")

        processed_count = 0
        skipped_count = 0
        processed_details = []

        for index, filename in enumerate(self.selected_files):
            if self.should_cancel:
                logging.warning("Обработка отменена пользователем")
                break

            # Обновляем прогресс
            self.progress_updated.emit(index, filename)

            file_path = os.path.join(UPLOADS_DIR, filename)
            output_filename = f"{os.path.splitext(filename)[0]}.txt"
            output_path = os.path.join(BASE_FOLDER, output_filename)

            # Проверяем, не обработан ли уже файл
            if os.path.exists(output_path):
                skipped_count += 1
                skip_message = f'Файл {filename} уже обработан (существует {output_filename})'
                processed_details.append(skip_message)
                self.file_processed.emit(filename, True, skip_message)
                logging.info(skip_message)
                continue

            logging.info(f"Обработка файла {index + 1}/{len(self.selected_files)}: {filename}")

            try:
                start_time = time.time()
                embeddings, count = process_docx_file(file_path)

                if count > 0:
                    save_embeddings_to_file(embeddings, output_path)

                    # Создаем резервную копию файла
                    backup_path = os.path.join(BACKUP_DIR, filename)
                    shutil.copy2(file_path, backup_path)

                    # Удаляем файл из uploads только после успешного создания резервной копии
                    os.remove(file_path)
                    processed_count += 1

                    elapsed_time = time.time() - start_time
                    status_message = f'Обработано: {filename} | Предложений: {count} | Время: {elapsed_time:.2f} сек.'
                    processed_details.append(status_message)
                    self.file_processed.emit(filename, True, status_message)
                    logging.info(status_message)
                else:
                    error_message = f'Файл {filename} не содержит текста для обработки'
                    processed_details.append(error_message)
                    self.file_processed.emit(filename, False, error_message)
                    logging.warning(error_message)

            except Exception as e:
                error_message = f'Ошибка при обработке {filename}: {str(e)}'
                processed_details.append(error_message)
                self.file_processed.emit(filename, False, error_message)
                logging.error(error_message, exc_info=True)

        # Завершаем обработку
        self.processing_finished.emit(processed_count, len(self.selected_files), skipped_count, processed_details)


def process_selected_files(file_list_layout, statusbar, main_window):
    """Обработать выбранные файлы и конвертировать их в эмбеддинги"""
    selected_files = []

    for i in range(file_list_layout.count()):
        widget = file_list_layout.itemAt(i).widget()
        if hasattr(widget, 'checkbox') and widget.checkbox.isChecked():
            selected_files.append(widget.filename)

    if not selected_files:
        statusbar.showMessage('Нет выбранных файлов')
        main_window.update_status('Нет выбранных файлов')
        logging.warning("Попытка обработки: нет выбранных файлов")
        return

    logging.info(f"Начало обработки {len(selected_files)} файлов")
    statusbar.showMessage(f'Начата обработка {len(selected_files)} файлов')
    main_window.update_status(f'Обработка {len(selected_files)} файлов...')

    # Создаем диалог прогресса
    progress = QProgressDialog("Подготовка к обработке...", "Отмена", 0, len(selected_files), main_window)
    progress.setWindowTitle("Прогресс обработки")
    progress.setWindowModality(Qt.WindowModal)
    progress.setMinimumDuration(0)  # Показывать сразу
    progress.show()

    # Создаем и запускаем поток обработки
    processing_thread = FileProcessingThread(selected_files)

    # Подключаем сигналы
    def update_progress(index, filename):
        progress.setValue(index)
        progress.setLabelText(f"Обработка файла: {filename}")
        statusbar.showMessage(f"Обработка: {filename}")

    def on_file_processed(filename, success, message):
        statusbar.showMessage(message)

    def on_processing_finished(processed_count, total_files, skipped_count, processed_details):
        progress.setValue(total_files)
        progress.close()

        # Показываем результат обработки
        show_processing_results(main_window, processed_count, total_files, skipped_count, processed_details)

        # Обновляем список файлов после обработки
        try:
            from file_operations import load_files
            load_files(
                main_window.file_list_layout,
                main_window.process_button,
                main_window.select_all_button,
                main_window.deselect_all_button,
                main_window.statusbar
            )
            main_window.update_status('Обработка завершена')
            logging.info("Список файлов обновлен после обработки")
        except Exception as e:
            logging.error(f"Ошибка при обновлении списка файлов: {e}")
            main_window.update_status('Обработка завершена (ошибка обновления списка)')

        logging.info(f"Завершена обработка. Успешно: {processed_count}/{total_files}, пропущено: {skipped_count}")

    def on_progress_canceled():
        processing_thread.cancel()
        processing_thread.wait()  # Ждем завершения потока
        statusbar.showMessage('Обработка отменена')
        main_window.update_status('Обработка отменена')

        # Обновляем список файлов
        try:
            from file_operations import load_files
            load_files(
                main_window.file_list_layout,
                main_window.process_button,
                main_window.select_all_button,
                main_window.deselect_all_button,
                main_window.statusbar
            )
        except Exception as e:
            logging.error(f"Ошибка при обновлении списка файлов: {e}")

    # Подключаем сигналы
    processing_thread.progress_updated.connect(update_progress)
    processing_thread.file_processed.connect(on_file_processed)
    processing_thread.processing_finished.connect(on_processing_finished)
    progress.canceled.connect(on_progress_canceled)

    # Запускаем поток
    processing_thread.start()


def show_processing_results(parent, processed_count, total_files, skipped_count, processed_details):
    """Показывает результаты обработки файлов"""
    try:
        msg_box = QMessageBox(parent)
        msg_box.setWindowTitle("Результат обработки")
        msg_box.setIcon(QMessageBox.Information)

        summary_text = f"Обработано файлов: {processed_count} из {total_files}\n"
        summary_text += f"Пропущено (уже обработаны): {skipped_count}\n\nДетали обработки:"

        for detail in processed_details:
            summary_text += f"\n• {detail}"

        msg_box.setText(summary_text)
        msg_box.setStandardButtons(QMessageBox.Ok)

        # Устанавливаем размер окна сообщения
        msg_box.setMinimumWidth(500)

        parent.statusbar.showMessage(f'Обработано: {processed_count}, пропущено: {skipped_count}')
        msg_box.exec_()

    except Exception as e:
        logging.error(f"Ошибка при показе результатов: {e}")
        # Fallback - показываем простое сообщение
        parent.statusbar.showMessage(f'Обработано: {processed_count}/{total_files}, пропущено: {skipped_count}')