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
check_url1 = myconfig['Check_wednesday']['check_url1']
check_url2 = myconfig['Check_wednesday']['check_url2']
try_cnt = myconfig['Check_wednesday']['try_cnt'] # 3
try_sleep = myconfig['Check_wednesday']['try_sleep'] # sec, use 5
sms_cmd = myconfig['SMS']['sms_cmd']
auth_tokens = myconfig['Check_wednesday'].get('auth_tokens', [])

# Thresholds
CRON_DATETIME_THRESHOLD_SEC = myconfig['Check_wednesday']['CRON_DATETIME_THRESHOLD_SEC'] # 10  # Maximum allowed time difference in seconds
OnTrade_DATETIME_THRESHOLD_SEC = myconfig['Check_wednesday']['OnTrade_DATETIME_THRESHOLD_SEC'] # 10  # Maximum allowed time difference in seconds
if_check_MEM = myconfig['Check_wednesday']['if_check_MEM']
MEM_AVAIL_THRESHOLD_PERCENT = myconfig['Check_wednesday']['MEM_AVAIL_THRESHOLD_PERCENT'] # 10.0  # Minimum allowed memory availability in percent

#
def check_json(_json_content):
    '''
# Example _json_content is in this format:
# one ["status"] dict
# many trade vendor dict under ["my_status"]["trade"]
# many quote vendor dict under ["my_status"]["quote"]
_json_content = {
  "status": {
    "cron_datetime": "2025-12-09 23:21:37.452",
    "boot_datetime": "2025-12-09 23:20:10.282",
    "OnContractDownloadComplete_datetime": "2025-12-09 22:02:43.146",
  },
  "my_status": {
    "trade": {
      "mega": {
        "order": true,
        "cron_datetime": "2025-12-09 23:21:32.608",
        "boot_datetime": "2025-12-09 22:02:33.930",
        "mem_free": "9.38G",
        "mem_avail": "58.65%",
      }
    },
    "quote": {
      "yuanta": {
        "quote": true,
        "order": true,
        "contracts": false,
        "regbook_num": 45,
        "tradebook_num": 45,
        "cron_datetime": "2025-12-09 23:21:37.042",
        "boot_datetime": "2025-12-09 22:09:29.114",
        "mem_free": "9.38G",
        "mem_avail": "58.66%",
        "response_time_ms": 6.124019622802734
      },
      "mega": {
        "quote": true,
        "contracts": true,
        "orderbook_num": 20,
        "tradebook_num": 3,
        "cron_datetime": "2025-12-09 23:21:34.384",
        "boot_datetime": "2025-12-09 22:02:33.930",
        "mem_free": "9.38G",
        "mem_avail": "58.65%",
        "response_time_ms": 1597.2049236297607
      }
    }
  }
}
'''

    try:
        current_datetime = datetime.now()
        
        # Helper function to check cron_datetime
        def check_cron_datetime(datetime_str, location_name):
            if not datetime_str:
                return {'result': False, 'msg': f'{location_name} cron_datetime is missing or empty'}
            
            if not isinstance(datetime_str, str):
                return {'result': False, 'msg': f'{location_name} cron_datetime is not a string'}
            
            try:
                cron_datetime = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S.%f")
            except Exception as e:
                return {'result': False, 'msg': f'{location_name} cron_datetime parse error: {str(e)}'}
            
            time_diff = abs((current_datetime - cron_datetime).total_seconds())
            if time_diff > CRON_DATETIME_THRESHOLD_SEC:
                return {'result': False, 'msg': f'{location_name} cron stop: {datetime_str}'}
            
            return {'result': True, 'msg': ''}
        
        # Helper function to check mem_avail
        def check_mem_avail(mem_avail_str, location_name):
            if not mem_avail_str:
                return {'result': False, 'msg': f'{location_name} mem_avail is missing or empty'}
            
            if not isinstance(mem_avail_str, str):
                return {'result': False, 'msg': f'{location_name} mem_avail is not a string'}
            
            try:
                # Remove '%' and convert to float
                mem_avail_value = float(mem_avail_str.rstrip('%'))
                if mem_avail_value < MEM_AVAIL_THRESHOLD_PERCENT:
                    return {'result': False, 'msg': f'{location_name} mem_avail too low: {mem_avail_str}'}
            except Exception as e:
                return {'result': False, 'msg': f'{location_name} mem_avail parse error: {str(e)}'}
            
            return {'result': True, 'msg': ''}
        
        # Check status cron_datetime
        status_dict = _json_content.get('status', {})
        if not status_dict:
            return {'result': False, 'msg': 'status section is missing'}
        
        status_cron_datetime_str = status_dict.get('cron_datetime', '')
        result = check_cron_datetime(status_cron_datetime_str, 'status')
        if not result['result']:
            return result
        
        # Check all trade vendors under my_status.trade
        trade_dict = _json_content.get('my_status', {}).get('trade', {})
        for vendor_name, vendor_data in trade_dict.items():
            if isinstance(vendor_data, dict):
                # Check cron_datetime
                vendor_cron_datetime_str = vendor_data.get('cron_datetime', '')
                result = check_cron_datetime(vendor_cron_datetime_str, f'trade.{vendor_name}')
                if not result['result']:
                    return result
                
                # Check mem_avail
                if if_check_MEM:
                    vendor_mem_avail_str = vendor_data.get('mem_avail', '')
                    result = check_mem_avail(vendor_mem_avail_str, f'trade.{vendor_name}')
                    if not result['result']:
                        return result
        
        # Check all quote vendors under my_status.quote
        quote_dict = _json_content.get('my_status', {}).get('quote', {})
        for vendor_name, vendor_data in quote_dict.items():
            if isinstance(vendor_data, dict):
                # Check cron_datetime
                vendor_cron_datetime_str = vendor_data.get('cron_datetime', '')
                result = check_cron_datetime(vendor_cron_datetime_str, f'quote.{vendor_name}')
                if not result['result']:
                    return result
                
                # Check mem_avail
                #vendor_mem_avail_str = vendor_data.get('mem_avail', '')
                #result = check_mem_avail(vendor_mem_avail_str, f'quote.{vendor_name}')
                #if not result['result']:
                #    return result
        
        return {'result': True, 'msg': ''}
        
    except Exception as e:
        return {'result': False, 'msg': f'Exception: {str(e)}'}

#
def check_json2(_json_content):
    '''
_json_content =
{
    "strategy_id": "FARR",
    "stocks": {
        "i00000": {
            "symbol_c": "i00000",
            "msg_time_c": "16:47:36",
            "bid1_price_c": "0",
            "match_price_c": "34861.1600",
            "time_value_c": 0,
            "ask1_price_c": "0",
            "match_time_c": "13:30:00",
            "strike_price": "-",
            "OnOrderBook_datetime": "-",
            "OnTrade_datetime": "2026-04-09 16:47:36.971331",
            "is_test_match": false
        }
    },
    "futures": {
        "MXFE6": {
            "symbol_c": "MXFE6",
            "msg_time_c": "18:54:58",
            "bid1_price_c": "34944",
            "match_price_c": "34944",
            "time_value_c": 0,
            "ask1_price_c": "34952",
            "match_time_c": "18:54:16",
            "strike_price": "-",
            "OnOrderBook_datetime": "-",
            "OnTrade_datetime": "2026-04-09 18:54:58.057716",
            "basis": 82.8,
            "is_test_match": false
        }
    },
    "options": {
        "34500": {
            "symbol_c": "TXO34500D6",
            "msg_time_c": "18:54:57",
            "bid1_price_c": "685.0",
            "match_price_c": "700.0",
            "ask1_price_c": "705.0",
            "match_time_c": "18:51:31",
            "OnOrderBook_datetime_c": "-",
            "OnTrade_datetime_c": "2026-04-09 18:54:57.569516",
            "intrinsic_value_c": 361.1600000000035,
            "time_value_c": 333.8399999999965,
            "intrinsic_value_future_c": 444.0,
            "time_value_future_c": 251.0,
            "is_test_match_c": false,
            "time_value_diff_future": -128.0,
            "strike_price": 34500,
            "match_time_p": "18:54:13",
            "ask1_price_p": "382.0",
            "match_price_p": "379.0",
            "bid1_price_p": "376.0",
            "msg_time_p": "18:54:56",
            "symbol_p": "TXO34500P6",
            "OnOrderBook_datetime_p": "-",
            "OnTrade_datetime_p": "2026-04-09 18:54:56.564626",
            "intrinsic_value_p": 0,
            "time_value_p": 379.0,
            "intrinsic_value_future_p": 0,
            "time_value_future_p": 379.0,
            "is_test_match_p": false,
            "time_value_diff": -45.16000000000349
        },
        ...
    }
}
'''
    #print(_json_content)
    try:
        # check stocks's elements, if now is btwn 09:00 and 13:30 and OnTrade_datetime is not empty, then check the time diff
        stocks_dict = _json_content.get('stocks', {})
        for stock_name, stock_data in stocks_dict.items():
            if isinstance(stock_data, dict):
                on_trade_datetime_str = stock_data.get('OnTrade_datetime', '')
                if on_trade_datetime_str:
                    #print(f'{stock_name} OnTrade_datetime: {on_trade_datetime_str}')
                    try:
                        on_trade_datetime = datetime.strptime(on_trade_datetime_str, "%Y-%m-%d %H:%M:%S.%f")
                        # Check if current time is between 09:00 and 13:30
                        now_time = datetime.now().time()
                        if now_time >= datetime.strptime("09:00:00", "%H:%M:%S").time() and now_time <= datetime.strptime("13:30:00", "%H:%M:%S").time():
                            # Check time difference between on_trade_datetime and current time
                            time_diff_sec = abs((datetime.now() - on_trade_datetime).total_seconds())
                            if time_diff_sec > OnTrade_DATETIME_THRESHOLD_SEC:
                                return {'result': False, 'msg': f'{_json_content["strategy_id"]} {stock_name} OnTrade_datetime too old: {on_trade_datetime_str}'}
                    except Exception as e:
                        return {'result': False, 'msg': f'{_json_content["strategy_id"]} {stock_name} datetime parse error: {str(e)}'}

        # check future's elements, if OnTrade_datetime is not empty, then check the time diff
        futures_dict = _json_content.get('futures', {})
        for future_name, future_data in futures_dict.items():
            if isinstance(future_data, dict):
                on_trade_datetime_str = future_data.get('OnTrade_datetime', '')
                
                if on_trade_datetime_str:
                    #print(f'{future_name} OnTrade_datetime: {on_trade_datetime_str}')
                    try:
                        on_trade_datetime = datetime.strptime(on_trade_datetime_str, "%Y-%m-%d %H:%M:%S.%f")
                        
                        # Check time difference between on_trade_datetime and current time
                        time_diff_sec = abs((datetime.now() - on_trade_datetime).total_seconds())
                        if time_diff_sec > OnTrade_DATETIME_THRESHOLD_SEC:
                            return {'result': False, 'msg': f'{_json_content["strategy_id"]} {future_name} OnTrade_datetime too old: {on_trade_datetime_str}'}
                    except Exception as e:
                        return {'result': False, 'msg': f'{_json_content["strategy_id"]} {future_name} datetime parse error: {str(e)}'}

        # finally
        return {'result': True, 'msg': ''}
        
    except Exception as e:
        return {'result': False, 'msg': f'Exception: {str(e)}'}



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
        
        # Try each auth token
        tokens_to_try = auth_tokens if auth_tokens else [None]
        for token in tokens_to_try:
            try:
                #print('a')
                headers = {}
                if token:
                    headers['Authorization'] = token
                
                response = requests.get(check_url, headers=headers, verify=False, timeout=3)
                # json_content
                json_content = response.json()
                result = check_json(json_content)
                # print(result)
                if not result['result']:
                    final_result = False
                    msg = datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ' ' + result['msg']
                else:
                    # Success with this token
                    final_result = True
                    msg = ''
                    
                # add another check
                # /get_strategy_id_quote NEAR
                if final_result:

                    response1 = requests.get(check_url1, headers=headers, verify=False, timeout=3)
                    is_trading_time = response1.json().get('is_trading_time', True) # default to True if key is missing

                    if is_trading_time: # is trading time

                        response = requests.post(check_url2, headers=headers, json={"strategy_id": "NEAR"}, verify=False, timeout=3)
                        # json_content
                        json_content = response.json()
                        result = check_json2(json_content)
                        # print(result)
                        if not result['result']:
                            final_result = False
                            msg = result['msg']
                        else:
                            # Success with this token
                            final_result = True
                            msg = ''

                # add another check
                # /get_strategy_id_quote FARR
                if final_result:

                    response1 = requests.get(check_url1, headers=headers, verify=False, timeout=3)
                    is_trading_time = response1.json().get('is_trading_time', True) # default to True if key is missing

                    if is_trading_time: # is trading time

                        response = requests.post(check_url2, headers=headers, json={"strategy_id": "FARR"}, verify=False, timeout=3)
                        # json_content
                        json_content = response.json()
                        result = check_json2(json_content)
                        # print(result)
                        if not result['result']:
                            final_result = False
                            msg = result['msg']
                        else:
                            # Success with this token
                            final_result = True
                            msg = ''

            except Exception as e:
                #print('b')
                final_result = False
                msg = datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ' exception: ' + str(e)
        
        if not final_result:
            time.sleep(try_sleep)

    # final result
    if not final_result:
        print(msg)
        curl_cmd = sms_cmd + ' -d text="wednesDay ' + msg + '"'
        rr = subprocess.run(curl_cmd, shell=True, capture_output=True, text=True)

    ## for test
    ## curl_cmd = '/usr/bin/curl -k -s -o /dev/null -X POST https://api.telegram.org/botXXX:YYY/sendMessage -d chat_id=1111111 -d text="' + str(0) + ' ' + lt_text[0] + '"'
    #curl_cmd = sms_cmd + ' -d text="' + str(0) + ' ' + lt_text[0] + '"'
    #rr = subprocess.run(curl_cmd, shell=True, capture_output=True, text=True)

    ## for test
    #import os
    #exit_status = os.system(curl_cmd)
    #time.sleep(10)



