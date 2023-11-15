#!/bin/bash
cd $HOME/venv
source py311/bin/activate
cd $HOME/life_codes/alert_sms
while true; do
  python check_friDay.py
  sleep 60
done
