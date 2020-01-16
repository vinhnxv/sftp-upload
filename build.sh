rm -rf build/
rm app.spec
rm -rf dist/
pyuic5 -x design/login.ui  -o design/login.py
pyuic5 -x design/uploader.ui  -o design/uploader.py
pyinstaller --windowed app.py --hidden-import PyQt5.sip
cp -rf text_unidecode dist/app/
