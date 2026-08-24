alert_sms_telegram
==================

Cron-driven monitoring. Small python scripts poll HTTP endpoints every few
minutes; when a service looks unhealthy they post an alert to a Telegram
channel. No server, no build step.

    check_friDay.py    host liveness on a plain-text status page
    check_wednesDay.py options-service freshness / memory / quote checks
    telegram_bot_*.py  long-polling Telegram bots (separate from the checks)

Config lives in config_requests.yml (gitignored; copy the .example).
Run with uv from the repo root:  uv run python check_wednesDay.py

See README.md for setup, check_friDay.txt / check_wednesDay.txt for what each
check does.
