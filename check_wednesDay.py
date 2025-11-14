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
check_url = myconfig['Check_wednesday']['check_url']
try_cnt = myconfig['Check_wednesday']['try_cnt'] # 3
try_sleep = myconfig['Check_wednesday']['try_sleep'] # sec, use 5
sms_cmd = myconfig['SMS']['sms_cmd']


#
def check_json(_json_content):
    '''
_json_content = {
  "status": {
    "main": {
      "boot_datetime": "2025-11-10 12:24:35.362",
      "cron_datetime": "2025-11-10 13:38:11.569",
      "OnContractDownloadComplete_datetime": "2025-11-10 11:59:44.882"
    },
    "quote": {
      "mega": {
        "is_pivot_out_of_strike": false,
        "normalized_position": 0.5,
        "quote_cho": "5",
        "quote_now": "5",
        "cron_datetime": "2025-11-10 13:38:10.702",
        "boot_datetime": "2025-11-10 11:59:33.896"
      }
    },
    "trade": {}
  }
}
'''
    try:
        _result = True
        _msg = ''
        current_datetime = datetime.now()
        
        # Check status cron_datetime
        status_cron_datetime_str = _json_content.get('summary', {}).get('main', {}).get('cron_datetime', '')
        if not status_cron_datetime_str:
            return {'result': False, 'msg': 'status cron_datetime is missing or empty'}
        
        if not isinstance(status_cron_datetime_str, str):
            return {'result': False, 'msg': 'status cron_datetime is not a string'}
        
        try:
            status_cron_datetime = datetime.strptime(status_cron_datetime_str, "%Y-%m-%d %H:%M:%S.%f")
        except Exception as e:
            return {'result': False, 'msg': f'status cron_datetime parse error: {str(e)}'}
        
        time_diff = abs((current_datetime - status_cron_datetime).total_seconds())
        if time_diff > 10:
            _result = False
            _msg = f"status cron stop: {status_cron_datetime_str}"
            return {'result': _result, 'msg': _msg}
        
        # Check all quote elements' cron_datetime
        quote_dict = _json_content.get('status', {}).get('quote', {})
        for element_name, element_data in quote_dict.items():
            if isinstance(element_data, dict):
                element_cron_datetime_str = element_data.get('cron_datetime', '')
                if not element_cron_datetime_str:
                    return {'result': False, 'msg': f'quote.{element_name} cron_datetime is missing or empty'}
                
                if not isinstance(element_cron_datetime_str, str):
                    return {'result': False, 'msg': f'quote.{element_name} cron_datetime is not a string'}
                
                try:
                    element_cron_datetime = datetime.strptime(element_cron_datetime_str, "%Y-%m-%d %H:%M:%S.%f")
                except Exception as e:
                    return {'result': False, 'msg': f'quote.{element_name} cron_datetime parse error: {str(e)}'}
                
                time_diff = abs((current_datetime - element_cron_datetime).total_seconds())
                if time_diff > 10:
                    _result = False
                    _msg = f"quote.{element_name} cron stop: {element_cron_datetime_str}"
                    return {'result': _result, 'msg': _msg}

        return {'result': _result, 'msg': _msg}
        
    except Exception as e:
        return {'result': False,
                'msg': str(e)}


if __name__ == "__main__":

    #%% start
    #print(check_url)
    #print(try_cnt)
    #print(try_sleep)

    i_cnt = 0
    final_result = False
    msg = ''
    while (final_result is False) and (i_cnt < try_cnt):
        #print(i_cnt)
        i_cnt = i_cnt + 1
        final_result = True
        try:
            #print('a')
            response = requests.get(check_url, verify=False, timeout=1)
            # json_content
            json_content = response.json()
            result = check_json(json_content)
            # print(result)
            if not result['result']:
                final_result = False
                msg = datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ' ' + result['msg']

        except Exception as e:
            #print('b')
            final_result = False
            msg = datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ' exception: ' + str(e)
        if not final_result:
            time.sleep(try_sleep)

    # final result
    if not final_result:
        print(msg)
        curl_cmd = sms_cmd + ' -d text="wednesDay error"'
        rr = subprocess.run(curl_cmd, shell=True, capture_output=True, text=True)

    ## for test
    ## curl_cmd = '/usr/bin/curl -k -s -o /dev/null -X POST https://api.telegram.org/botXXX:YYY/sendMessage -d chat_id=1111111 -d text="' + str(0) + ' ' + lt_text[0] + '"'
    #curl_cmd = sms_cmd + ' -d text="' + str(0) + ' ' + lt_text[0] + '"'
    #rr = subprocess.run(curl_cmd, shell=True, capture_output=True, text=True)

    ## for test
    #import os
    #exit_status = os.system(curl_cmd)
    #time.sleep(10)



