import yaml
from concurrent.futures import ThreadPoolExecutor
import requests
from datetime import datetime, timedelta
import re 
import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()
import time
import subprocess

# config
def get_myconfig(_myconfig_file):
    with open(_myconfig_file, 'r', encoding="utf-8") as stream:
        _myconfig = yaml.load(stream, Loader=yaml.CLoader)
    return _myconfig
#myconfig = get_myconfig("config.yml")
myconfig = get_myconfig("config_requests.yml")
getget_url = myconfig['Check']['getget_url']
try_cnt = myconfig['Check']['try_cnt'] # 3
try_sleep = myconfig['Check']['try_sleep'] # sec, use 60
sms_cmd = myconfig['SMS']['sms_cmd']


#
'''
2025-01-22 14:31:00 39_fastapi_peering_local
2025-01-23 10:53:52 39_fastapi_peering_468office 22
2025-01-23 10:54:03 39_fastapi_peering_468idc
2025-01-23 10:54:39 39_fastapi_peering_AZtaiwan 31 32
2025-01-22 13:07:13 39_fastapi_peering_AZtokyo
2025-01-23 10:54:44 39_fastapi_peering_outside
'''
def check_line(line):
    try:
        # Split line into timestamp and message
        parts = line.split(' ', 2)
        if len(parts) < 3:
            return False
            
        # Check if it's one of the monitored services
        monitored_services = [
          #  '39_fastapi_peering_local',
            '39_fastapi_peering_468office',
            '39_fastapi_peering_468idc',
            '39_fastapi_peering_AZtaiwan',
          #  '39_fastapi_peering_AZtokyo',
            '39_fastapi_peering_outside'
        ]
        
        service = parts[2].split()[0]  # Get service name without numbers
        if service not in monitored_services:
            return True  # Skip validation for non-monitored services
            
        # Check if there are numbers after service name
        if len(parts[2].split()) > 1:
            return False
            
        # Check timestamp
        timestamp = datetime.strptime(f"{parts[0]} {parts[1]}", '%Y-%m-%d %H:%M:%S')
        time_diff = datetime.now() - timestamp
        if time_diff > timedelta(minutes=5):
            #print('aaa')
            return False
            
        return True # Everything is OK
        
    except Exception:
        return False

#%% start
#print(getget_url)
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
    lt_text = msg.splitlines()

    with ThreadPoolExecutor() as executor:
      results = executor.map(check_line, lt_text)

      for result in results:
        #print(type(result))
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
  print(msg)
  curl_cmd = sms_cmd + ' -d text="friDay error"'
  rr = subprocess.run(curl_cmd, shell=True, capture_output=True, text=True)

## for test
## curl_cmd = '/usr/bin/curl -k -s -o /dev/null -X POST https://api.telegram.org/bot6666240541:AAFHp3SQNqTyKycVcCegkR5R75P5YuKgRuc/sendMessage -d chat_id=6543018944 -d text="' + str(0) + ' ' + lt_text[0] + '"'
#curl_cmd = sms_cmd + ' -d text="' + str(0) + ' ' + lt_text[0] + '"'
#rr = subprocess.run(curl_cmd, shell=True, capture_output=True, text=True)

## for test
#import os
#exit_status = os.system(curl_cmd)
#time.sleep(10)



