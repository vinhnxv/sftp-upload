import paramiko


class SFTPClient(object):
    def __init__(self, host, port, username, password, key_file_path, key_file_type):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.key_file_path = key_file_path
        self.key_file_type = key_file_type
        self.connection = self.get()

    def get(self):
        sftp = None
        key = None
        transport = None
        try:
            if self.key_file_path is not None:
                # Get private key used to authenticate user.
                if self.key_file_type == 'DSA':
                    # The private key is a DSA type key.
                    key = paramiko.DSSKey.from_private_key_file(self.key_file_path)
                else:
                    # The private key is a RSA type key.
                    key = paramiko.RSAKey.from_private_key(self.key_file_path)

            # Create Transport object using supplied method of authentication.
            transport = paramiko.Transport((self.host, self.port))
            transport.connect(username=self.username, password=self.password, pkey=key)

            sftp = paramiko.SFTPClient.from_transport(transport)

            return sftp
        except Exception as err:
            print('An error occurred creating SFTP client: %s: %s' % (err.__class__, err))
            if sftp is not None:
                sftp.close()
            if transport is not None:
                transport.close()
            raise err

    def listdir(self):
        return self.connection.listdir('.')

    def upload_file(self, local_file, remote_file, callback=None):
        self.connection.put(local_file, remote_file, callback=callback)

    def close(self):
        self.connection.close()
