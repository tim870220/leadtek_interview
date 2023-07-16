#!/bin/bash

# 安裝 Python 3.9
sudo apt-get update
sudo apt-get install python3.9

# 安裝 pip
sudo apt-get install python3-pip

# 安裝所需的 Python 模組
pip3 install -r requirements.txt

# 安裝 MariaDB
sudo apt-get update
sudo apt-get install -y mariadb-server

# 設定 root 使用者的密碼
# sudo mysql -u root -e "SET PASSWORD FOR 'root'@'localhost' = PASSWORD('00000000');"

# 使用 root 使用者建立新資料庫 leadtek
# sudo mysql -u root -p00000000 -e "CREATE DATABASE leadtek;"

# 建立資料庫 leadtek (方法2)
# mysql -u root -p00000000 <<EOF
# CREATE DATABASE leadtek;
# EOF
