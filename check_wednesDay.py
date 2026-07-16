"""wednesDay options-service health check.

Two kinds of check, alerting via Telegram on the first failure found:

1. ``/info``      - service + per-vendor ``cron_datetime`` freshness and, for
                    trade vendors, ``mem_avail``.
2. ``/get_strategy_id_quote`` for each strategy - ``OnOrderBook_datetime``
                    freshness of stocks (only during market hours) and futures.
                    Skipped entirely when ``/is_trading_time`` is false.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time as dtime

import requests

from alert_common import (
    CheckResult,
    load_config,
    now_stamp,
    run_with_retries,
    send_telegram_alert,
)

CONFIG_FILE = "config_requests.yml"
MARKET_OPEN = dtime(9, 0, 10)
MARKET_CLOSE = dtime(13, 29, 50)
DATETIME_FMT = "%Y-%m-%d %H:%M:%S.%f"


@dataclass
class Config:
    check_url: str
    trading_time_url: str
    quote_url: str
    try_cnt: int
    try_sleep: float
    auth_tokens: list
    monitored_strategies: list
    cron_threshold_sec: float
    orderbook_threshold_sec: float
    check_mem: bool
    mem_avail_threshold_pct: float

    @classmethod
    def from_section(cls, w: dict) -> "Config":
        return cls(
            check_url=w["check_url"],
            trading_time_url=w["check_url1"],
            quote_url=w["check_url2"],
            try_cnt=w.get("try_cnt", 3),
            try_sleep=w.get("try_sleep", 5),
            auth_tokens=w.get("auth_tokens") or [],
            monitored_strategies=w.get("monitored_strategies") or [],
            cron_threshold_sec=w.get("CRON_DATETIME_THRESHOLD_SEC", 30),
            orderbook_threshold_sec=w.get("OnOrderBook_datetime_THRESHOLD_SEC", 30),
            check_mem=w.get("if_check_MEM", True),
            mem_avail_threshold_pct=w.get("MEM_AVAIL_THRESHOLD_PERCENT", 10.0),
        )


def _age_seconds(value: str) -> float:
    return abs((datetime.now() - datetime.strptime(value, DATETIME_FMT)).total_seconds())


# --- /info checks -----------------------------------------------------------

def _check_cron(value: object, where: str, cfg: Config) -> CheckResult:
    if not isinstance(value, str) or not value:
        return CheckResult(False, f"{where} cron_datetime is missing or invalid")
    try:
        age = _age_seconds(value)
    except ValueError as exc:
        return CheckResult(False, f"{where} cron_datetime parse error: {exc}")
    if age > cfg.cron_threshold_sec:
        return CheckResult(False, f"{where} cron stop: {value}")
    return CheckResult(True)


def _check_mem(value: object, where: str, cfg: Config) -> CheckResult:
    if not isinstance(value, str) or not value:
        return CheckResult(False, f"{where} mem_avail is missing or invalid")
    try:
        pct = float(value.rstrip("%"))
    except ValueError as exc:
        return CheckResult(False, f"{where} mem_avail parse error: {exc}")
    if pct < cfg.mem_avail_threshold_pct:
        return CheckResult(False, f"{where} mem_avail too low: {value}")
    return CheckResult(True)


def check_status(data: dict, cfg: Config) -> CheckResult:
    status = data.get("status") or {}
    if not status:
        return CheckResult(False, "status section is missing")

    result = _check_cron(status.get("cron_datetime"), "status", cfg)
    if not result.ok:
        return result

    my_status = data.get("my_status", {})
    # mem_avail is only meaningful for trade vendors (matches original behaviour).
    for section, check_mem in (("trade", cfg.check_mem), ("quote", False)):
        for vendor, vdata in (my_status.get(section) or {}).items():
            if not isinstance(vdata, dict):
                continue
            result = _check_cron(vdata.get("cron_datetime"), f"{section}.{vendor}", cfg)
            if not result.ok:
                return result
            if check_mem:
                result = _check_mem(vdata.get("mem_avail"), f"{section}.{vendor}", cfg)
                if not result.ok:
                    return result
    return CheckResult(True)


# --- /get_strategy_id_quote checks ------------------------------------------

def _check_orderbook(item: object, strategy: str, name: str, cfg: Config) -> CheckResult:
    if not isinstance(item, dict):
        return CheckResult(True)
    value = item.get("OnOrderBook_datetime")
    if not value:
        return CheckResult(True)
    try:
        age = _age_seconds(value)
    except ValueError as exc:
        return CheckResult(False, f"{strategy} {name} datetime parse error: {exc}")
    if age > cfg.orderbook_threshold_sec:
        return CheckResult(False, f"{strategy} {name} OnOrderBook_datetime too old: {value}")
    return CheckResult(True)


def check_quote(data: dict, cfg: Config) -> CheckResult:
    strategy = data.get("strategy_id", "?")
    in_market_hours = MARKET_OPEN <= datetime.now().time() <= MARKET_CLOSE

    # Stocks trade only during market hours; futures are checked regardless.
    if in_market_hours:
        for name, item in (data.get("stocks") or {}).items():
            result = _check_orderbook(item, strategy, name, cfg)
            if not result.ok:
                return result

    for name, item in (data.get("futures") or {}).items():
        result = _check_orderbook(item, strategy, name, cfg)
        if not result.ok:
            return result

    return CheckResult(True)


def check_strategies(headers: dict, cfg: Config) -> CheckResult:
    is_trading = (
        requests.get(cfg.trading_time_url, headers=headers, verify=False, timeout=3)
        .json()
        .get("is_trading_time", True)
    )
    if not is_trading:
        return CheckResult(True)
    for strategy in cfg.monitored_strategies:
        data = requests.post(
            cfg.quote_url,
            headers=headers,
            json={"strategy_id": strategy},
            verify=False,
            timeout=3,
        ).json()
        result = check_quote(data, cfg)
        if not result.ok:
            return result
    return CheckResult(True)


def run_once(cfg: Config) -> CheckResult:
    """One full pass, trying each auth token until one fully succeeds."""
    tokens = cfg.auth_tokens or [None]
    last = CheckResult(False, "no auth token configured")
    for token in tokens:
        headers = {"Authorization": token} if token else {}
        try:
            data = requests.get(
                cfg.check_url, headers=headers, verify=False, timeout=3
            ).json()
            result = check_status(data, cfg)
            if not result.ok:
                last = CheckResult(False, f"{now_stamp()} {result.msg}")
                continue

            result = check_strategies(headers, cfg)
            if not result.ok:
                last = result
                continue

            return CheckResult(True)
        except Exception as exc:  # noqa: BLE001 - try the next token, then retry
            last = CheckResult(False, f"{now_stamp()} exception: {exc}")
    return last


def main() -> None:
    raw = load_config(CONFIG_FILE)
    cfg = Config.from_section(raw["Check_wednesday"])
    sms_cmd = raw["Check_wednesday"]["sms_cmd"]

    result = run_with_retries(
        lambda: run_once(cfg),
        try_cnt=cfg.try_cnt,
        try_sleep=cfg.try_sleep,
    )

    if not result.ok:
        print(result.msg)
        send_telegram_alert(sms_cmd, f"wednesDay {result.msg}")


if __name__ == "__main__":
    main()
