from concurrent.futures import ThreadPoolExecutor
import requests
from datetime import datetime, timedelta
import re 
import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()
import time

#
def check_line(line):
  if not re.fullmatch(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} OK', line):
    print("Rule 1 failed")
    return False

  dt = datetime.strptime(line.split(' ')[0] + ' ' + line.split(' ')[1], '%Y-%m-%d %H:%M:%S') 
  now = datetime.now()
  diff = now - dt

  if diff > timedelta(minutes=2):
    print("Rule 2 failed")
    return False

  return True

#
url = 'https://ailog.shopping.friday.tw/getget'

try_cnt = 3
final_result = False
i_cnt = 0
while (final_result is False) and (i_cnt < try_cnt):
  print(i_cnt)
  i_cnt = i_cnt + 1
  final_result = True
  try:
    response = requests.get(url, verify=False)
    msg = response.text
    text = response.text.splitlines()

    with ThreadPoolExecutor() as executor:
      results = executor.map(check_line, text)

    for result in results:
      if not result:
        #print("Check failed")
        #print(response.text)
        final_result = False
        #exit(False)
  except:
    final_result = False
    msg = 'exception'
  if not final_result:
    time.sleep(5)


print(msg)
print(final_result)  
exit(True)
