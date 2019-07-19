#!/bin/bash
sudo apt-get install python3-pip -y
sleep 10
pip3 install hvac
sleep 10
python3 create_groups.py
