# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Small cron-driven monitoring project. Scripts poll HTTP endpoints, and if a service
looks unhealthy, alert to a Telegram channel. There is no server, no build step, and
no automated test suite.

Two independent script families share one uv environment:

1. **Health checks** (`check_friDay.py`, `check_wednesDay.py`) — the primary use case.
   Requests-based, run one-shot from cron, alert via Telegram.
2. **Telegram bots** (`telegram_bot_eye.py`, `telegram_bot_example.py`) — long-polling
   `python-telegram-bot` apps, run as long-lived background processes. Largely separate
   from the checks.

## Commands

Dependencies are managed with **uv** (`pyproject.toml` + `uv.lock`); there is no pip/venv workflow.

```bash
uv sync                              # create .venv and install deps
uv run python check_wednesDay.py     # run a check directly (from repo root)
uv run python check_friDay.py
uv run python telegram_bot_eye.py    # run a bot (foreground)
```

Always run from the repo root: config file paths and the `alert_common` import are
relative to the working directory. The `.sh` wrappers `cd` into the repo and call
`uv run` for exactly this reason.

There is no lint config and no test framework. To sanity-check the pure check logic,
feed sample payloads (see the docstrings in each script) directly to the `check_*`
functions rather than hitting the network.

## Architecture

**Shared core — `alert_common.py`.** Both check scripts build on:
- `CheckResult(ok: bool, msg: str)` — every check function returns this; `ok=False`
  carries a human-readable failure `msg`.
- `run_with_retries(check, try_cnt, try_sleep)` — calls a zero-arg `check` callable
  until it returns `ok`, or attempts are exhausted. **Exceptions raised by `check`
  (network/JSON errors) are caught here and count as a failed attempt**, so individual
  check functions don't need their own top-level try/except for retry purposes.
- `send_telegram_alert(sms_cmd, text)` — appends the message as a separate curl argument
  via `shlex.split` (no `shell=True`), so alert text can never inject into the shell.

**Check script shape.** Each `check_*.py` is thin: define check function(s) returning
`CheckResult`, then `main()` loads config, calls `run_with_retries`, and on final failure
prints the message and sends a Telegram alert prefixed with the weekday name
(`"friDay ..."` / `"wednesDay ..."`). Only a failing final result produces an alert —
success is silent.

- `check_friDay.py` — polls a plain-text endpoint of `<date> <time> <host> [reason]`
  lines. A host in the config's `monitored_hosts` list is unhealthy when any text is
  appended after its name. Non-timestamp lines (trailing free-text failure section) are
  ignored. Monitored hosts are **config-driven**, not hardcoded.
- `check_wednesDay.py` — options-service checks. Loads its section into a `Config`
  dataclass (`Config.from_section`, using `.get` defaults so missing keys don't crash).
  Two check kinds: `check_status` (cron_datetime freshness + trade-vendor mem_avail from
  `/info`) and `check_quote` (OnOrderBook_datetime freshness per strategy from
  `/get_strategy_id_quote`, gated by `/is_trading_time` and market-hours). Tries each
  entry in `auth_tokens` until one fully succeeds.

**Configuration.** Runtime config lives in `config_requests.yml` (checks) and
`config_telegrambot.yml` (bots). **Both are gitignored** because they hold the real bot
token, chat_id, and auth tokens; only the `*.yml.example` files are tracked. When adding
a config key, update both the active file and its `.example`. Adjusting check behavior
(monitored hosts, thresholds, URLs, retries) is a config edit, not a code edit.

**Deployment.** `crontab.txt` documents the schedule; cron runs `check_*.sh`, which
`cd` into the repo and `uv run` the corresponding script, appending output to `logs/`.

## Git

`origin` is a **multi-mirror remote** — pushes fan out to GitLab, GitHub, and Bitbucket
in a single `git push`.
