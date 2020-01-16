import json
import os

from cryptography.fernet import Fernet

from .const import LOGIN_FILE, KEY


class Auth(object):
    def __init__(self, host='', port=22, username='', password='', directory=''):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.directory = directory
        self.ciphered_text = b''

    def encrypted(self):
        cipher_suite = Fernet(KEY)
        auth_information = json.dumps(dict(
            host=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
            directory=self.directory,
        ))
        byte_auth = bytes(auth_information, 'utf-8')
        return cipher_suite.encrypt(byte_auth)

    def store_login_file(self):
        with open(LOGIN_FILE, 'wb') as file_object:
            file_object.write(self.encrypted())

    def read_login_file(self):
        if os.path.isfile(LOGIN_FILE):
            cipher_suite = Fernet(KEY)
            encrypted_pwd = None
            with open(LOGIN_FILE, 'rb') as file_object:
                for line in file_object:
                    encrypted_pwd = line

            if encrypted_pwd:
                decrypt_text = cipher_suite.decrypt(encrypted_pwd)

                # convert to string
                auth_text = bytes(decrypt_text).decode("utf-8")
                auth = json.loads(auth_text)

                # Set property
                if 'host' in auth and 'port' in auth and 'username' in auth and 'password' in auth and 'directory' in auth:
                    self.host = auth['host']
                    self.port = auth['port']
                    self.username = auth['username']
                    self.password = auth['password']
                    self.directory = auth['directory']

                    return auth

        return None
