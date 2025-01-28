
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

# Configuration File (config.yml):
Begin by copying config_requests.yml.example to config.yml

# Do the necessary modification. In the check section, set the following parameters:

Check:
  getget_url: 'https://aaa.bbb.com/api'
  try_cnt: 3
  try_sleep: 30 # 30 seconds

The getget_url should return the following format (in text/html):

Successful responses:
2025-01-22 14:31:00 39_fastapi_peering_local
2025-01-27 11:43:17 39_fastapi_peering_AZtaiwan
2025-01-27 11:43:28 39_fastapi_peering_outside
... some more lines

Unsuccessful responses (accompanied by error codes):
2025-01-22 14:31:00 39_fastapi_peering_local 13 20
2025-01-27 11:43:17 39_fastapi_peering_AZtaiwan 13
2025-01-27 11:43:28 39_fastapi_peering_outside 13
... some more lines

# In the SMS section, set the following parameters:

SMS:
  sms_cmd: 'curl -k -s -o /dev/null -X POST https://api.telegram.org/botXXX:YYY/sendMessage -d chat_id=ZZZ '

Instead of SMS, we've transitioned to using Telegram for its cost-effectiveness. Inside check_friDay.py, the shell command is as follows:
$ curl -k -s -o /dev/null -X POST https://api.telegram.org/botXXX:YYY/sendMessage -d chat_id=ZZZ -d text="alert!text!"

# set up environment
$ cd $HOME/venv
$ /filepath/python3.11 -m venv --system-site-packages py311
$ source py311/bin/activate
$ pip install --upgrade pip
$ cd $HOME/life_codes/alert_sms_telegram # filepath_of_this_project
$ pip install -r requirements_requests_py311.txt

# Cron Job, example of cron command is in crontab.txt:
*/5 * * * * $HOME/life_codes/alert_sms_telegram/check_friDay.sh >> /tmp/jie_aa.txt 2>&1 


## 3. a python-telegram-bot example


# set up environment

$ cd $HOME/venv
$ /filepath/python3.7 -m venv --system-site-packages py37t
$ source py37t/bin/activate
$ pip install --upgrade pip
$ pip install -r requirements_telegrambot_py37

# run the 'long polling' mode for telegram bot (there is also webhooks)

$ cd $HOME/venv
$ source py37t/bin/activate
$ $HOME/life_codes/alert_sms_telegram # filepath_of_this_project
$ python telegram_bot_example.py

# misc memo

#in /home/pi/MiTemperature2/sendToInflux_eyepi.sh
#you should have:
mkdir -p /tmp/sensor
echo $3 > /tmp/sensor/$2


## 3. a telegram bot example
cp config_telegrambot.yml.example config_telegrambot.yml