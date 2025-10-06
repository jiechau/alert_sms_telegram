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
    "quote": false,
    "order": false,
    "contracts": true,
    "cron": {
        "is_trading_time": false,
        "is_serving_time": true,
        "IsConnectedLive_quote": false,
        "IsConnectedLive_order": false,
        "cron_exception": "",
        "cron_datetime": "2023-10-07 07:28:15.416"
    },
    "quote_api": {
        "IsConnected": false,
        "logonOK": false,
        "LastErrorMsg": "",
        "OnConnected_datetime": "2023-10-06 22:26:51.227",
        "OnDisconnected_datetime": "2023-10-07 05:30:04.500",
        "LogonOK_datetime": "2023-10-06 22:26:51.402",
        "LogonFail_datetime": "",
        "OnLogonResponseOK_ReplyString": "Logon OK!",
        "OnLogonResponseOK_datetime": "2023-10-06 22:26:51.412",
        "OnLogonResponseFail_ReplyString": "",
        "OnLogonResponseFail_datetime": "",
        "contracts": true,
        "OnContractDownloadComplete_datetime": "2023-10-06 22:26:58.046"
    },
    "order_api": {
        "EnableMEGACA": true,
        "IsConnected": false,
        "logonOK": false,
        "SetAccountOK": false,
        "LastErrorMsg": "",
        "EnableMEGACAOK_datetime": "2023-10-06 22:26:50.664",
        "EnableMEGACAFail_datetime": "",
        "OnConnected_datetime": "2023-10-06 22:26:52.830",
        "OnDisconnected_datetime": "2023-10-07 05:00:00.469",
        "logonProxyOK_datetime": "2023-10-06 22:26:53.503",
        "logonProxyFail_datetime": "",
        "OnLogonResponseOK_ReplyString": "Login Mega DMA OK!( CID =46 )...logon ok",
        "OnLogonResponseOK_datetime": "2023-10-06 22:26:53.911",
        "OnLogonResponseFail_ReplyString": "",
        "OnLogonResponseFail_datetime": "",
        "SetAccountOK_datetime": "2023-10-06 22:26:54.511",
        "SetAccountFail_datetime": ""
    }
}
'''
    try:
        _result = True
        _msg = ''
        # Check if cron_datetime is within 10 seconds of current time
        cron_datetime_str = _json_content.get('cron', {}).get('cron_datetime', '')
        if cron_datetime_str:
            cron_datetime = datetime.strptime(cron_datetime_str, "%Y-%m-%d %H:%M:%S.%f")
            #print(cron_datetime)
            current_datetime = datetime.now()
            time_diff = abs((current_datetime - cron_datetime).total_seconds())
            if time_diff > 10:
                _result = False
                _msg = f"cron stop: {cron_datetime_str}"

        return {'result': _result,
                'msg': _msg}
        # return True # Everything is OK
        
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
            if not result:
                final_result = False

        except:
            #print('b')
            final_result = False
            msg = datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ' exception'
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



