# -*- coding: utf-8 -*-
import os
import json
import sys
from Utils import IOUtil,Log


__baseBalance = 0
__quoteBalance = 1500

__logFile = "./Log/balance.log"

__balanceFile = './Data/balance'

def __LoadBalance():
    """
    加载资产数据，如果数据文件不存在，则初始化资产数据
    """
    global __baseBalance,__quoteBalance
    
    if os.path.exists(__balanceFile):
        try:
            jsonStr = IOUtil.ReadTextFromFile(__balanceFile)
            jsonData = json.loads(jsonStr)
            __baseBalance = jsonData['baseBalance']
            __quoteBalance = jsonData['quoteBalance']
        except Exception as e:
            Log.Print("Fatal Error , can not load balance file! ",e)
            Log.Info(__logFile,"Fatal Error, Can not load balance file! " + str(e))
            sys.exit()     
    else:
        balanceData = json.dumps({'baseBalance':__baseBalance,'quoteBalance':__quoteBalance})
        IOUtil.WriteTextToFile(__balanceFile,balanceData)

def __SaveBalance():
    """
    保存资产数据
    """
    global __baseBalance,__quoteBalance
    balanceData = json.dumps({'baseBalance':__baseBalance,'quoteBalance':__quoteBalance})
    IOUtil.WriteTextToFile(__balanceFile,balanceData)





def Start():
    __LoadBalance()


__LoadBalance()
