#!/bin/bash
ff_pid=$(ps -ef | grep "telegram_bot_eye.py" | grep -v 'grep' | awk '{print $2}')
if [ ! -z "$ff_pid" ]; then
    kill -9 $ff_pid
fi
source $HOME/venv/py37t/bin/activate
cd $HOME/life_codes/alert_sms_telegram
#python3 telegram_bot_eye.py >> /tmp/telegram_bot_eye.log 2>&1 &
python3 telegram_bot_eye.py > /dev/null 2>&1 &

