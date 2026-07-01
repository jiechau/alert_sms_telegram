"""friDay peering health check.

Polls a plain-text status endpoint and alerts via Telegram when any monitored
host reports a failure reason appended after its name.

Each status line looks like:  ``2026-07-01 15:33:50 k8s06``
A failing host carries a trailing reason:  ``2026-07-01 15:37:32 gpu168 connection``

The response may also contain a trailing free-text section (a dashed separator
followed by failure details); those non-status lines are ignored.
"""
from __future__ import annotations

from datetime import datetime

import requests

from alert_common import (
    CheckResult,
    load_config,
    run_with_retries,
    send_telegram_alert,
)

CONFIG_FILE = "config_requests.yml"


def check_line(line: str, monitored_hosts: set[str]) -> CheckResult:
    parts = line.split(" ", 2)
    if len(parts) < 3:
        return CheckResult(True)  # not a status line -> ignore

    try:
        datetime.strptime(f"{parts[0]} {parts[1]}", "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return CheckResult(True)  # not a status line -> ignore

    host, *reason = parts[2].split()
    if host not in monitored_hosts:
        return CheckResult(True)  # not monitored -> ignore
    if reason:
        return CheckResult(False, line)  # failure reason appended
    return CheckResult(True)


def check_endpoint(url: str, monitored_hosts: set[str]) -> CheckResult:
    lines = requests.get(url, verify=False, timeout=2).text.splitlines()
    if not lines:
        return CheckResult(False, "no data received from endpoint")
    for line in lines:
        result = check_line(line, monitored_hosts)
        if not result.ok:
            return result
    return CheckResult(True)


def main() -> None:
    cfg = load_config(CONFIG_FILE)
    section = cfg["Check_friday"]
    sms_cmd = cfg["SMS"]["sms_cmd"]
    monitored_hosts = set(section.get("monitored_hosts") or [])

    result = run_with_retries(
        lambda: check_endpoint(section["check_url"], monitored_hosts),
        try_cnt=section["try_cnt"],
        try_sleep=section["try_sleep"],
    )

    if not result.ok:
        print(result.msg)
        send_telegram_alert(sms_cmd, f"friDay {result.msg}")


if __name__ == "__main__":
    main()
