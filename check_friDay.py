from concurrent.futures import ThreadPoolExecutor
import requests
from datetime import datetime, timedelta
import re 
import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()

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

response = requests.get(url, verify=False)
text = response.text.splitlines()

with ThreadPoolExecutor() as executor:
  results = executor.map(check_line, text)

for result in results:
  if not result:
    print("Check failed")
    print(response.text)
    exit(False)

print("All checks passed")  
exit(True)
