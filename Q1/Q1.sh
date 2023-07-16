#!/bin/bash

# 安裝 Python 3.9
sudo apt-get update
sudo apt-get install python3.9

# 安裝 pip
sudo apt-get install python3-pip

# 安裝所需的 Python 模組
pip3 install -r requirements.txt
