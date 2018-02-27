# -*- coding: utf-8 -*-

import DataDownloader
import BalanceManager
import time
from Utils import IOUtil, Log
import os, sys
import json
from API.Huobi import HuobiServices

def InitSystem():
    """
    加载密钥，初始化交易所服务
    获取Account id，赋值到交易所服务
    """
    configFile = "Config.json"
  
    try:    
        configJsonStr = IOUtil.ReadTextFromFile(configFile)
        configData = json.loads(configJsonStr)
        access_key = configData['access_key']
        secret_key = configData['secret_key']
        HuobiServices.init_key(access_key,secret_key)

        accounts = HuobiServices.get_accounts()
        account_id = accounts['data'][0]['id']
        HuobiServices.init_account(account_id)

        HuobiServices.init_symbols()
        
    except Exception as e:
        Log.Print("Fatal Error: Init system faild!\nException: ",e)
        sys.exit()


def RecoverSystem():
    pass

def StartSystem():
    RecoverSystem()
    DataDownloader.Start()
    BalanceManager.Start()


def DoStrategy():
    print("Do Strategy")

"""
if __name__ == '__main__':
    InitSystem()
    StartModules()
    
    while(True):
        DoStrategy()
        time.sleep(1)

"""

InitSystem()

#print(HuobiServices.get_spot_balance('btc'))

#print(HuobiServices.get_amount_precision('bcxbtc'))
#print(HuobiServices.get_price_precision('bcxbtc'))
'''

{'status': 'ok', 'data': '1876107434'}
'''
#orderData = HuobiServices.send_order(1,'api','eosusdt','sell-limit',18)
def OrderSendHandle(jsonData):
    try:
        status = jsonData['status']
        if status == 'ok':
            orderId = jsonData['data']
            Log.Print("SUCCESS! Order Send, orderId:{}".format(orderId))
            # TODO: Log.Info
            return orderId
        else:
            Log.Print("FAILD! Order Send, status:{} rawData:{}".format(status,jsonData))
            # TODO: Log.Info
            return None
    except Exception as e:
        Log.Print("EXCEPTION: Parse order send result data faild: rawData:{}".format(jsonData))
        # TODO: Log.Info

#print(orderData)
#print("")
#OrderSendHandle(orderData)

#orderData = HuobiServices.order_info('1876107434')

'''
{'status': 'ok', 'data': {'id': 1876107434, 'symbol': 'eosusdt', 'account-id': 634980, 'amount': '1.000000000000000000', 'price': '18.000000000000000000', 'created-at': 1519710682948, 'type': 'sell-limit', 'field-amount': '0.0', 'field-cash-amount': '0.0', 'field-fees': '0.0', 'finished-at': 0, 'source': 'api', 'state': 'submitted', 'canceled-at': 0}}
'''

def OrderInfoHandle(jsonData):
    try:
        status = jsonData['status']
        if status == 'ok':
            # parse data
            orderId = jsonData['data']['id']
            symbol = jsonData['data']['symbol']
            state = jsonData['data']['state']
            print(orderId,symbol,state)
            return orderId,symbol,state
        else:
            Log.Print("FAILD! Check order info, status:{} rawData:{}".format(status,jsonData))
            # TODO: Log.Info
    except Exception as e:
        Log.Print("EXCEPTION: Parse order info result data faild: rawData:{}".format(jsonData))
        # TODO: Log.Info


#OrderInfoHandle(orderData)

orderData = HuobiServices.cancel_order('1876107434')
print(orderData)

orderData = HuobiServices.order_info('1876107434')
print(orderData)
OrderInfoHandle(orderData)
