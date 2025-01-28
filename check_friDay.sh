#!/bin/bash

#cd $HOME/venv
#source py311/bin/activate
#cd $HOME/life_codes/alert_sms_telegram
#while true; do
#  python check_friDay.py
#  sleep 60
#done


cd $HOME/venv
source py311/bin/activate
cd $HOME/life_codes/alert_sms_telegram
python check_friDay.py >> logs/sms.txt 2>&1
deactivate
current_time=$(date +"done %Y-%m-%d %H:%M:%S")
echo $current_time >> logs/sms.txt
