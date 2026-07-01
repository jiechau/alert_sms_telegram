#!/bin/bash
export PATH="$HOME/.local/bin:$PATH"  # cron has a minimal PATH; uv lives here
cd $HOME/life_codes/alert_sms_telegram
uv run python check_friDay.py >> logs/check_friDay.txt 2>&1
current_time=$(date +"done %Y-%m-%d %H:%M:%S")
echo $current_time >> logs/check_friDay.txt
