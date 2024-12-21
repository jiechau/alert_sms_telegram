#!/bin/bash
ff_pid=$(ps -ef | grep "python telegram_bot_eye.py" | grep -v 'grep' | awk '{print $2}')
kill -9 $ff_pid
source $HOME/py37t/bin/activate
cd $HOME/life_codes/alert_sms_telegram
python3 telegram_bot_eye.py >> /tmp/telegram_bot_eye.log 2>&1 &

