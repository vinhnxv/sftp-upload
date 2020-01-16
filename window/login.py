from PySide2.QtWidgets import QMainWindow, QDesktopWidget, QMessageBox

from design import Ui_LoginWindow
from utils import message_box
from .auth import Auth
from .sftp import SFTPClient
from .uploader import UploaderWindow


class LoginWindow(QMainWindow):
    uploader_window = None

    def __init__(self, parent=None):
        super(LoginWindow, self).__init__(parent)

        self.ui = Ui_LoginWindow()
        self.ui.setupUi(self)
        self.ui.login_button.clicked.connect(self.login)
        self.ui.exit_button.clicked.connect(self.close)

        # center screen
        self.move(QDesktopWidget().availableGeometry().center() - self.frameGeometry().center())

        # init uploader window
        self.uploader_window = UploaderWindow()

        # get previous login
        auth = self.get_login_file()
        if auth:
            self.ui.host_text_edit.setText(auth['host'])
            self.ui.port_text_edit.setText(str(auth['port']))
            self.ui.username_text_edit.setText(auth['username'])
            self.ui.password_text_edit.setText(auth['password'])
            self.ui.directory_text_edit.setText(auth['directory'])

    def check_login(self, host, port, username, password):
        """
        :param host: host
        :param port: port
        :param username: username
        :param password: password
        :return: True or False
        """
        field = ''
        if not host:
            field = 'host'
        elif not port:
            field = 'port'
        elif not username:
            field = 'username'
        elif not password:
            field = 'password'

        if field:
            message_box(self, 'Error', 'The %s is required' % field, QMessageBox.Critical)
            return False

        return True

    def login(self):
        host = self.ui.host_text_edit.text()
        port = int(self.ui.port_text_edit.text())
        username = self.ui.username_text_edit.text()
        password = self.ui.password_text_edit.text()
        directory = self.ui.directory_text_edit.text()

        if self.check_login(host, port, username, password):
            try:
                sftp = SFTPClient(host, port, username, password, None, 'DSA')
                sftp.close()
                self.open_uploader_window(host, port, username, password, directory)
                return True
            except Exception as err:
                message_box(self, 'Error', str(err), QMessageBox.Critical)
                return False

    def open_uploader_window(self, host='', port=22, username='', password='', directory=''):
        # store login file
        self.store_login_file(host, port, username, password, directory)

        # hide login window
        self.hide()

        # open uploader window
        if self.uploader_window:
            self.uploader_window.set_params(host, port, username, password, directory)
        else:
            self.uploader_window = UploaderWindow(host=host, port=port, username=username, password=password, directory=directory)
        self.uploader_window.show()
        self.uploader_window.ui.logout_menu_action.triggered.connect(self.logout_uploader_form)

    def logout_uploader_form(self):
        self.show()
        if self.uploader_window:
            self.uploader_window.close()

    def store_login_file(self, host, port, username, password, directory):
        auth = Auth(host, port, username, password, directory)
        auth.store_login_file()

    def get_login_file(self):
        auth = Auth()
        return auth.read_login_file()
