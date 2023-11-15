import yaml
from concurrent.futures import ThreadPoolExecutor
import requests
from datetime import datetime, timedelta
import re 
import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()
import time


# config
def get_myconfig(_myconfig_file):
    with open(_myconfig_file, 'r', encoding="utf-8") as stream:
        _myconfig = yaml.load(stream, Loader=yaml.CLoader)
    return _myconfig
myconfig = get_myconfig("config.yml")
getget_url = myconfig['Check']['getget_url']
getget_lines = myconfig['Check']['getget_lines']
try_cnt = myconfig['Check']['try_cnt'] # 3
try_sleep = myconfig['Check']['try_sleep'] # sec, use 60
sms_url = myconfig['SMS']['sms_url']
sms_username = myconfig['SMS']['sms_username']
sms_password = myconfig['SMS']['sms_password']
sms_defaultdst = myconfig['SMS']['sms_defaultdst']


#
def check_line(line):
  if not re.fullmatch(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} OK', line):
    #print("Rule 1 failed")
    return False

  dt = datetime.strptime(line.split(' ')[0] + ' ' + line.split(' ')[1], '%Y-%m-%d %H:%M:%S') 
  now = datetime.now()
  diff = now - dt

  if diff > timedelta(minutes=2):
    #print("Rule 2 failed")
    return False

  return True

#%% start
#print(getget_url)
#print(getget_lines)
#print(try_cnt)
#print(try_sleep)


i_cnt = 0
final_result = False
while (final_result is False) and (i_cnt < try_cnt):
  #print(i_cnt)
  i_cnt = i_cnt + 1
  final_result = True
  try:
    response = requests.get(getget_url, verify=False)
    msg = response.text
    lt_text = msg.splitlines()[:2]

    with ThreadPoolExecutor() as executor:
      results = executor.map(check_line, lt_text)

    for result in results:
      if not result:
        #print("Check failed")
        #print(response.text)
        final_result = False
        #exit(False)
  except:
    final_result = False
    msg = datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ' exception'
  if not final_result:
    time.sleep(try_sleep)

# final result
if not final_result:
  #print(msg)
  lt_text = msg.splitlines()[:2]
  for i in range(len(lt_text)):
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} OK', lt_text[i]):
      print(str(i) + ' ' + lt_text[i])
  

