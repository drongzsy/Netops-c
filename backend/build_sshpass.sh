#!/bin/bash
set -e
cd /tmp
sudo apt-get install -y sshpass 2>/dev/null && echo "SSHPASS_INSTALLED" && exit 0
wget -q https://sourceforge.net/projects/sshpass/files/sshpass/1.10/sshpass-1.10.tar.gz/download -O sshpass.tar.gz
tar xzf sshpass.tar.gz
cd sshpass-1.10
./configure --prefix=$HOME/.local
make
make install
echo "SSHPASS_BUILT"
