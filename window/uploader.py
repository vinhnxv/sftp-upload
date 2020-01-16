import os
from time import time

from PySide2.QtCore import *
from PySide2.QtCore import Qt
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from hurry.filesize import size as change_size
from slugify import slugify

from design import Ui_UploaderWindow
from utils import message_box
from .sftp import SFTPClient
from .worker import Worker

COL_NUMBER = 2


class UploaderWindow(QMainWindow):
    def __init__(self, parent=None, host='', port=22, username='', password='', directory=''):
        super(UploaderWindow, self).__init__(parent)
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.directory = directory

        # Config UI
        self.ui = Ui_UploaderWindow()
        self.ui.setupUi(self)
        self.ui.choose_file_button.clicked.connect(self.open_file_dialog)
        self.ui.exit_button.clicked.connect(self.close)
        self.ui.upload_button.clicked.connect(self.upload)
        self.ui.add_button.clicked.connect(self.add)
        self.ui.delete_button.clicked.connect(self.delete)
        self.ui.progress_bar.hide()

        self.ui.upload_button.setDisabled(True)
        self.ui.delete_button.setDisabled(True)

        # create table
        self.create_table()

        # center screen
        self.move(QDesktopWidget().availableGeometry().center() - self.frameGeometry().center())

        # create qt thread pool
        self.thread_pool = QThreadPool()
        print("Multithreading with maximum %d threads" % self.thread_pool.maxThreadCount())

    def set_params(self, host, port, username, password, directory):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.directory = directory

    def open_file_dialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_name, _ = QFileDialog.getOpenFileName(self, "Choose movie file", "",
                                                   "File mp4 (*.mp4);;Python Files (*.mp4)", options=options)
        if file_name:
            self.ui.path_edit.setText(file_name)

    def upload(self):
        if self.row_count() > 0:
            try:
                # Connect ftp
                sftp = SFTPClient(self.host, self.port, self.username, self.password, None, 'DSA')

                if self.directory:
                    sftp.connection.chdir(self.directory)

                # create directory
                if not self.create_directory(sftp):
                    return False

                # upload media
                self.upload_media(sftp)

                return True
            except Exception as err:
                message_box(self, 'Error', str(err), QMessageBox.Critical)
                return False

    def add(self):
        if self.check_add():
            self.add_row()
            self.clear()

    def delete(self):
        self.delete_selected_rows()

    def directory_exists(self, sftp, dir_name):
        try:
            sftp.connection.chdir(dir_name)
            return True
        except IOError:
            return False

    def create_directory(self, sftp):
        try:
            title, _ = self.get_first_row_data()
            if title:
                title = slugify(title, separator=" ")
                if not self.directory_exists(sftp, title):
                    # create new directory
                    sftp.connection.mkdir(title)
                    sftp.connection.chdir(title)
                return True
        except Exception as err:
            message_box(self, 'Error', str(err), QMessageBox.Critical)
            return False

    def upload_media(self, sftp):
        try:
            name, file_path = self.get_first_row_data()
            self.start_upload_file_thread(sftp, name, file_path)

        except Exception as err:
            message_box(self, 'Error', str(err), QMessageBox.Critical)
        return False

    def check_add(self):
        title = self.ui.movie_name_edit.text()
        if not title:
            message_box(self, 'Error', 'Movie name is required!', QMessageBox.Critical)
            return False

        file_path = self.ui.path_edit.text()
        if not file_path or not os.path.isfile(file_path):
            message_box(self, 'Error', 'Media file not found!', QMessageBox.Critical)
            return False
        return True

    def upload_done(self):
        self.remove_first_row()
        if self.row_count() > 0:
            self.ui.progress_bar.setValue(0)
            self.upload()
        else:
            # hide progress bar
            self.ui.progress_bar.hide()
            self.statusBar().showMessage('')
            self.ui.delete_button.setDisabled(True)
            message_box(self, 'OK', 'Upload successfully!', QMessageBox.Information)

    def clear(self):
        self.ui.movie_name_edit.setText('')
        self.ui.path_edit.setText('')

    def get_ts_name(self, title, ts):
        return slugify(str(ts) + '-' + title)

    def upload_file_progress(self, size):
        _, file_path = self.get_first_row_data()
        total_size = os.path.getsize(file_path)
        percent = size / total_size * 100

        # show progress bar and reset value
        self.ui.progress_bar.setValue(percent)
        self.statusBar().showMessage('Uploading...%s...%s%%...' % (change_size(size), int(percent)))

    def execute_upload_file(self, sftp, title, file_path, ts, progress_callback):
        file_size = os.path.getsize(file_path)

        # create ftp handle
        ftp_handle = FTPHandler(file_size, progress_callback)

        sftp.upload_file(file_path, '%s.mp4' % self.get_ts_name(title, ts), callback=ftp_handle.update)

        # quit ftp
        sftp.close()

        return "Done."

    def print_upload_file_output(self):
        # reset ui
        self.upload_done()

    @staticmethod
    def thread_upload_file_complete():
        print("THREAD COMPLETE!")

    def start_upload_file_thread(self, ftp, title, file_path):
        # Disable UI
        self.ui.upload_button.setDisabled(True)
        self.set_active_row_download()
        self.disable_first_row()
        self.ui.progress_bar.show()

        # Pass the function to execute
        ts = time()
        worker = Worker(self.execute_upload_file, ftp, title, file_path, ts)
        worker.signals.result.connect(self.print_upload_file_output)
        worker.signals.finished.connect(self.thread_upload_file_complete)
        worker.signals.progress.connect(self.upload_file_progress)

        # Execute
        self.thread_pool.start(worker)

    def get_first_row_data(self):
        name = self.ui.table_widget.item(0, 0).text()
        file_path = self.ui.table_widget.item(0, 1).text()
        return name, file_path

    def create_table(self):
        # Create table
        self.ui.table_widget.setColumnCount(COL_NUMBER)
        # set header label
        self.ui.table_widget.setHorizontalHeaderLabels(['Name', 'File Path'])

        self.ui.table_widget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.ui.table_widget.verticalHeader().hide()

        self.ui.table_widget.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.ui.table_widget.setFixedHeight(200)

        # select rows, not cell
        self.ui.table_widget.setSelectionBehavior(QTableView.SelectRows)

        # single selection
        self.ui.table_widget.setSelectionMode(QAbstractItemView.SingleSelection)

        self.ui.table_widget.move(0, 0)

    def add_row(self):
        # Retrieve text from QLineEdit
        name = self.ui.movie_name_edit.text()
        movie_path = self.ui.path_edit.text()

        # Create a empty row at bottom of table
        num_rows = self.row_count()
        self.ui.table_widget.insertRow(num_rows)
        # Add text to the row
        self.ui.table_widget.setItem(num_rows, 0, QTableWidgetItem(name))
        self.ui.table_widget.setItem(num_rows, 1, QTableWidgetItem(movie_path))
        self.ui.table_widget.resizeColumnsToContents()
        self.ui.table_widget.setVisible(True)

        self.ui.delete_button.setDisabled(False)
        self.ui.upload_button.setDisabled(False)

    def set_table_width(self):
        width = self.ui.table_widget.verticalHeader().width()
        width += self.ui.table_widget.horizontalHeader().length()
        if self.ui.table_widget.verticalScrollBar().isVisible():
            width += self.ui.table_widget.verticalScrollBar().width()
        width += self.ui.table_widget.frameWidth() * 2
        self.ui.table_widget.setFixedWidth(width)

    def remove_first_row(self):
        self.ui.table_widget.removeRow(0)

    def set_active_row_download(self):
        for index in range(0, COL_NUMBER):
            self.ui.table_widget.item(0, index).setBackground(QColor(125, 125, 125))

    def delete_selected_rows(self):
        indices = self.ui.table_widget.selectionModel().selectedRows()
        for index in sorted(indices):
            if index != 0:
                self.ui.table_widget.removeRow(index.row())

    def row_count(self):
        return self.ui.table_widget.rowCount()

    def disable_first_row(self):
        for index in range(0, COL_NUMBER):
            item = self.ui.table_widget.item(0, index)
            item.setFlags(Qt.NoItemFlags)


class FTPHandler(object):
    def __init__(self, total_size=0, progress_callback=None):
        self.total_size = total_size
        self.progress_callback = progress_callback

    def update(self, size, file_size):
        self.progress_callback.emit(size)
