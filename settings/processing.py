import os
import time
import logging
import shutil

from PyQt5 import Qt
from PyQt5.QtWidgets import QProgressDialog, QMessageBox
from base import process_docx_file, save_embeddings_to_file, BASE_FOLDER
from settings import UPLOADS_DIR, BACKUP_DIR

def process_selected_files(file_list_layout, statusbar, main_window):
    """Обработать выбранные файлы и конвертировать их в эмбеддинги"""
    selected_files = []

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

    progress = QProgressDialog("Обработка файлов...", "Отмена", 0, len(selected_files), main_window)
    progress.setWindowTitle("Прогресс обработки")
    progress.setWindowModality(Qt.WindowModal)
    progress.show()

    if not os.path.exists(BASE_FOLDER):
        os.makedirs(BASE_FOLDER)
        logging.info(f"Создана папка {BASE_FOLDER}")

    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
        logging.info(f"Создана папка {BACKUP_DIR}")

    processed_count = 0
    skipped_count = 0
    processed_details = []

    for index, filename in enumerate(selected_files):
        progress.setValue(index)
        progress.setLabelText(f"Обработка файла: {filename}")

        if progress.wasCanceled():
            logging.warning("Обработка отменена пользователем")
            break

        file_path = os.path.join(UPLOADS_DIR, filename)
        output_filename = f"{os.path.splitext(filename)[0]}.txt"
        output_path = os.path.join(BASE_FOLDER, output_filename)

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
            embeddings, count = process_docx_file(file_path)

            if count > 0:
                save_embeddings_to_file(embeddings, output_path)
                backup_path = os.path.join(BACKUP_DIR, filename)
                shutil.copy2(file_path, backup_path)
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

    progress.setValue(len(selected_files))

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