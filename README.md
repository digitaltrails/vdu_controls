

python3 -m build

Prerequisites:

zypper install python38-QtPy
zypper install ddcutil
lsmod | grep i2c-dev
modprobe i2c-dev

cd docs
make man html