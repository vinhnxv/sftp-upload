# SFTP Media Upload

## Required environment
* Qt 5.12.6
* python 3.7.6
* virtualenv


## Installation

Setup virtual env
```
$ [sudo] pip install virtualenv
```

Create VE with python3
```
virtualenv -p python3 env
```
Use created VE
```
source env/bin/activate
```

### pip install
```
pip install -r requirements.txt
```

### Build UI
```
pyside2-uic -x design/login.ui  -o design/login.py
pyside2-uic -x design/uploader.ui  -o design/uploader.py
```

### Run  
```
python app.py
```

## Deploy
```
chmod +x build.sh
./build.sh
```

## Create SFTP User
### Step 1 – Create User

First of all, create a user account to use for sftp access. Below command will create user named vinhnx with no shell access.

```
sudo adduser --shell /bin/false vinhnx
```

### Step 2 – Create Directory for SFTP
Now, create the directory structure to be accessible by sftp user.
```bash
sudo mkdir -p /var/vinhnx/upload
```

Change the ownership of the files directory to sftp user. So that sftp user can read and write on this directory.
```bash
sudo chown vinhnx:vinhnx /var/vinhnx/upload
```

And set the owner and group owner of the /var/vinhnx to root. The root user has read/write access on this access. Group member and other account have only read and execute permissions.

```bash
sudo chown root:root /var/vinhnx
sudo chmod 755 /var/vinhnx
```

### Step 3 – Configure SSH for SFTP Only
Now edit the SSH configuration file in a text editor
```bash
sudo vim /etc/ssh/sshd_config
```

and add the following settings at end of file.
```
Match User vinhnx
	ForceCommand internal-sftp
	PasswordAuthentication yes
	ChrootDirectory /var/vinhnx
	PermitTunnel no
	AllowAgentForwarding no
	AllowTcpForwarding no
	X11Forwarding no
```

Save the configuration and restart SSH service to apply changes.
``` bash
sudo systemctl restart ssh
```
