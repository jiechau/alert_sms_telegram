#!/bin/bash
export PATH="$HOME/.local/bin:$PATH"  # cron has a minimal PATH; uv lives here
cd $HOME/life_codes/alert_sms_telegram
uv run python check_wednesDay.py >> logs/check_wednesDay.txt 2>&1
current_time=$(date +"done %Y-%m-%d %H:%M:%S")
echo $current_time >> logs/check_wednesDay.txt
