ook

## 1. Setting up Telegram

one bot

(1) Install Telegram.

(2) Add BotFather (https://telegram.me/BotFather). Use the /newbot command to create a bot (e.g., @aaaBot). 
    After this, you'll receive a secret token in the format 68998798798:AAh2cFwDKdh2c2CJAh2c (This is your XXX:YYY).

(3) Access BotFather again using /mybots, select your bot (@aaaBot), and adjust the settings:

	Go to 'Bot Settings'
	Select 'Channel Admin Rights'
	Enable 'Post in the channel' (make it checked)

many channels

(4) Create a new channel (private or public), for instance 'my_alert_channel' with an invite code like https://t.me/+abcdefghijklmn

(5) Configure my_alert_channel by adding @aaaBot as an admin.

(6) Send a message to my_alert_channel, something simple like 'kkk'.

(7) Find the chat_id using a Linux terminal:

	$ curl https://api.telegram.org/botXXX:YYY/getUpdates
	or 
	$ curl https://api.telegram.org/botXXX:YYY/getUpdates | grep 'kkk'
	
	The chat_id will appear in a format such as '452452341' or '-61341341' (This is your ZZZ).

	another way:
	Forward a message from your channel to @userinfobot
	you can get your chat_id
	但是這裏要小心，很多假的，要找那個每月使用量很大的那個就是了

(8) Now, with XXX, YYY, ZZZ obtained, you can send messages to 'my_alert_channel' using:

	$ curl -k -s -o /dev/null -X POST https://api.telegram.org/botXXX:YYY/sendMessage -d chat_id=ZZZ -d text='alert!text!' # don't use double quote




## 2. a python requests example

The checks share the same shape: poll an endpoint, and if it looks stale/unhealthy,
retry a few times before firing a Telegram alert. check_friDay.py and
check_wednesDay.py are thin scripts; the shared retry / alert / config helpers
live in alert_common.py. We'll use check_wednesDay.py as the example.

# Configuration File (config_requests.yml):
Begin by copying config_requests.yml.example to config_requests.yml

# Do the necessary modification. In the Check_wednesday section, set the parameters:

Check_wednesday:
  check_url:  'https://options/info'              # service + per-vendor status
  check_url1: 'https://options/is_trading_time'   # gate the quote checks
  check_url2: 'https://options/get_strategy_quote' # per-strategy quotes (POST)
  CRON_DATETIME_THRESHOLD_SEC: 30                  # max cron_datetime age (sec)
  OnOrderBook_datetime_THRESHOLD_SEC: 30           # max OnOrderBook age (sec)
  if_check_MEM: True                               # also check trade mem_avail
  MEM_AVAIL_THRESHOLD_PERCENT: 10.0                # min free memory (percent)
  try_cnt: 3
  try_sleep: 5 # seconds between retries
  auth_tokens:
    - 'Basic XXXXX='   # tried in order until one succeeds

check_url returns JSON. check_wednesDay.py flags a failure when:
  - status / any vendor cron_datetime is older than CRON_DATETIME_THRESHOLD_SEC
  - a trade vendor's mem_avail drops below MEM_AVAIL_THRESHOLD_PERCENT
  - during market hours, a stock / future OnOrderBook_datetime is too old
    (only when /is_trading_time reports is_trading_time = true)

Healthy /info looks like:
{
  "status": {"cron_datetime": "2025-12-09 23:21:37.452"},
  "my_status": {
    "trade": {"mega":   {"cron_datetime": "2025-12-09 23:21:32.608", "mem_avail": "58.65%"}},
    "quote": {"yuanta": {"cron_datetime": "2025-12-09 23:21:37.042"}}
  }
}

An unhealthy response is one where a cron_datetime lags, or a POST to
check_url2 returns a strategy whose OnOrderBook_datetime is stale.

# In the SMS section, set the following parameters:

SMS:
  sms_cmd: 'curl -k -s -o /dev/null -X POST https://api.telegram.org/botXXX:YYY/sendMessage -d chat_id=ZZZ '

Instead of SMS, we've transitioned to using Telegram for its cost-effectiveness.
The alert text is appended to sms_cmd as a separate argument (no shell quoting),
so the effective command is:
$ curl -k -s -o /dev/null -X POST https://api.telegram.org/botXXX:YYY/sendMessage -d chat_id=ZZZ -d text='wednesDay <failure message>'

# set up environment (uv)
Install uv once (https://docs.astral.sh/uv/): curl -LsSf https://astral.sh/uv/install.sh | sh
$ cd $HOME/life_codes/alert_sms_telegram # filepath_of_this_project
$ uv sync   # creates .venv and installs deps from pyproject.toml

# run it
$ uv run python check_wednesDay.py
The check_wednesDay.sh / check_friDay.sh wrappers already call `uv run`, so no
manual activate/deactivate is needed.

# Cron Job, example of cron command is in crontab.txt:
*/1 * * * * $HOME/life_codes/alert_sms_telegram/check_wednesDay.sh >> /tmp/log_check_wednesDay.txt 2>&1


## 3. a python-telegram-bot example


# set up environment (uv)
python-telegram-bot is already declared in pyproject.toml, so the same uv
environment used by the check_* scripts covers the bot too.

$ cd $HOME/life_codes/alert_sms_telegram # filepath_of_this_project
$ uv sync   # creates .venv and installs deps from pyproject.toml

# run the 'long polling' mode for telegram bot (there is also webhooks)

$ cd $HOME/life_codes/alert_sms_telegram # filepath_of_this_project
$ uv run python telegram_bot_example.py

The telegram_bot_eye.sh wrapper also uses `uv run`, so it needs no manual
activate/deactivate.

# misc memo

#in /home/pi/MiTemperature2/sendToInflux_eyepi.sh
#you should have:
mkdir -p /tmp/sensor
echo $3 > /tmp/sensor/$2


## 3. a telegram bot example
cp config_telegrambot.yml.example config_telegrambot.yml