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

