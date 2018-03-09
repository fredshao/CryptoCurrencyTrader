# -*- coding: utf-8 -*-
import json
from API.Huobi import HuobiServices
from Utils import IOUtil, Log
import os, sys




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


InitSystem()

print("System Inited")

#orderData = HuobiServices.send_order(1,'api','elfusdt','sell-limit',0.7171)
orderData = HuobiServices.order_info('2168816738')
print(orderData)

