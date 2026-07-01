"""Shared helpers for the check_* health-check / Telegram alert scripts."""
from __future__ import annotations

import shlex
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable

import urllib3
import yaml

# The endpoints we poll use self-signed certs and are hit with verify=False.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


@dataclass
class CheckResult:
    """Outcome of a single check: ok=True means healthy, msg explains a failure."""

    ok: bool
    msg: str = ""


def load_config(path: str | Path) -> dict:
    with open(path, encoding="utf-8") as stream:
        return yaml.safe_load(stream)


def now_stamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def run_with_retries(
    check: Callable[[], CheckResult], *, try_cnt: int, try_sleep: float
) -> CheckResult:
    """Run ``check`` until it succeeds or ``try_cnt`` attempts are exhausted.

    Any exception raised by ``check`` (network / parse errors) counts as a
    failed attempt and is retried after ``try_sleep`` seconds.
    """
    result = CheckResult(False, "no attempts made")
    for attempt in range(1, try_cnt + 1):
        try:
            result = check()
        except Exception as exc:  # noqa: BLE001 - any failure is retryable
            result = CheckResult(False, f"{now_stamp()} exception: {exc}")
        if result.ok:
            return result
        if attempt < try_cnt:
            time.sleep(try_sleep)
    return result


def send_telegram_alert(sms_cmd: str, text: str) -> None:
    """Send ``text`` via the configured curl command.

    ``sms_cmd`` is the curl invocation from config (without the message body);
    the text is appended as a separate argument so message content can never
    break out of / inject into the shell command.
    """
    cmd = shlex.split(sms_cmd) + ["-d", f"text={text}"]
    subprocess.run(cmd, capture_output=True, text=True)
