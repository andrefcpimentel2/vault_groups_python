#!/bin/bash
echo demo | sudo -S apt-get install python3-pip -y && pip3 install hvac && python3 ./create_groups.py
