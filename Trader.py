# -*- coding: utf-8 -*-

import DataDownloader
import BalanceManager
import OrderManager
import HoldManager
import time
from Utils import IOUtil, Log
import os, sys
import json
from API.Huobi import HuobiServices
import numpy as np
from datetime import datetime
import Const


"""
基本流程是这样的
买入操作:
Start模块判断是否需要买入，如果是，调用BalanceManager操作资金，然后调用OrderManager执行买入
如果买入成交，OrderManager模块则会调用HoldManager创建持有
如果买入下单失败，OrderManager则要调用BalanceManager模块回滚资金

卖出操作:
Start模块根据策略判断现在是否是卖出时机，如果是，则会调用HoldManager获取所有可以卖出的持有
然后调用OrderManager模块进行下单
下单成功，OrderManager模块要回调HoldManager模块修改持有的状态
下单失败，OrderManager模块要回调HoldManager模块修改持有的状态
下单成交，OrderManager模块要回调HoldManager模块修改持有的状态
"""


class Probe:
    """
    proberType: 0 下降探针，1 上升探针
    proberLevel: 1~9，依次表示下降幅度
    proberPrice: 探针触发值
    """
    def __init__(self,probeType,probePrice,probeLevel):
        self.probeType = probeType
        self.probePrice = probePrice
        self.probeLevel = probeLevel
    
    def Triggered(self,price):
        if self.probeType == 0: # 下降探针
            if price < self.probePrice:
                return True
            else:
                return False
        else: # 上升探针
            if price > self.probePrice:
                return True
            else:
                return False


def SetProbe(price,probeType,lastTriggeredProbe = None):
    if probeType == 0:
        # 设置下降探针
        if lastTriggeredProbe != None and lastTriggeredProbe.probeType == 0:
            lastProbeLevel = lastTriggeredProbe.probeLevel
            currProbeLevel = lastProbeLevel * 1.2
        else:
            currProbeLevel = 150
            
        p = Probe(probeType,price - currProbeLevel,currProbeLevel)
    else:
        # 布置上升探针
        if lastTriggeredProbe != None and lastTriggeredProbe.probeType == 1:
            lastProbeLevel = lastTriggeredProbe.probeLevel
            currProbeLevel = lastProbeLevel * 1.1
        else:
            currProbeLevel = 100
        p = Probe(probeType,price + currProbeLevel,currProbeLevel)
    logStr = "Set Probe: probeType:{} price:{} probeLevel:{} probePrice:{}".format(probeType,price, currProbeLevel, p.probePrice)
    Log.Print(logStr)
    Log.Info(Const.logFile,logStr)
    return p


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
        logStr = "Fatal Error: Init System Faild!\n Exception:{}".format(e)
        Log.Print(logStr)
        Log.Info(Const.logFile,logStr)
        sys.exit()


def StartSystem():
    """
    启动各子系统
    """
    HoldManager.Start()
    DataDownloader.Start()
    BalanceManager.Start()
    OrderManager.Start()


def StopSystem():
    """
    停止各子系统
    """
    OrderManager.Stop()
    DataDownloader.Stop()

def TryToBuy(price):
    """
    这里尝试买入，因为想要尽量快点成交，所以这里比第一卖出价出更高的价格买入
    先判断一定时间内，是否有比当前价格更低的买入还没有卖出去
    再判断是否有和当前价格相差在150usdt之内的买入
    再检查资金是否足够
    """
    price += 1

    dtNow = datetime.now()
    rangeSeconds = 4 * 3600
    count = 0
    for hold in HoldManager.holds:
        dtHold = hold.buyTime
        timeDiff = (dtNow - dtHold).seconds
        if timeDiff < rangeSeconds:
            if hold.buyPrice < price:
                count += 1

        priceDiff = abs(hold.buyPrice - price)
        if priceDiff < 150:
            return False

    if count >= 2:
        return False

    costQuote, buyAmount = BalanceManager.Buy(price)
    if costQuote < 0 or buyAmount < 0:
        return False
    
    operationId = str(time.time())
    OrderManager.SendBuy(operationId,price,buyAmount, costQuote)
    return True

def TryToSell(price):
    """
    这里尝试买入，因为想要尽量快点成交，所以这里要卖的便宜一点，比最低的买入者价格再低一1usdt
    """
    price -= 1
    index = 0
    canSellList = HoldManager.GetCanSellHolds(price)
    if canSellList != None and len(canSellList) > 0:
        for hold in canSellList:
            index += 1
            operationId = hold.operationId
            OrderManager.SendSell(operationId,price,hold.holdAmount,hold.buyCost)
    

def Terminated():
    if os.path.exists("terminated"):
        return True
    return False


declineProbe = None
riseProbe = None

if __name__ == '__main__':
    InitSystem()
    StartSystem()
    logStr = "All System Started!"
    Log.Print(logStr)
    Log.Info(Const.logFile,logStr)
    while(True):
        if Terminated():
            break

        if DataDownloader.DataValid() and len(DataDownloader.realTimeBids) > 0:
            currBidPrice = DataDownloader.realTimeBids[-1]
            TryToSell(currBidPrice)

            currAskPrice = DataDownloader.realTimeAsks[-1]
            if declineProbe == None and riseProbe == None:
                declineProbe = SetProbe(currAskPrice,0)
                riseProbe = SetProbe(currAskPrice,1)
            else:
                if len(DataDownloader.realTimeAsks) < 60:
                    time.sleep(0.5)
                    continue

                meanPrice = np.mean(DataDownloader.realTimeAsks[-10:])
                if declineProbe.Triggered(meanPrice):
                    declineProbe = SetProbe(currAskPrice,0,declineProbe)
                    riseProbe = SetProbe(currAskPrice,1)
                    logStr = "-----> Try To Buy: {}".format(currAskPrice)
                    Log.Print(logStr)
                    Log.Info(Const.logFile,logStr)
                    TryToBuy(currAskPrice)
                elif riseProbe.Triggered(meanPrice):
                    declineProbe = SetProbe(currAskPrice,0)
                    riseProbe = SetProbe(currAskPrice,1,riseProbe)
        time.sleep(0.5)
    StopSystem()
    logStr = "!!!Terminated System Ready to Shutdown!!!!"
    Log.Print(logStr)
    Log.Info(Const.logFile,logStr)
    time.sleep(20)




#print(HuobiServices.get_spot_balance('btc'))

#print(HuobiServices.get_amount_precision('bcxbtc'))
#print(HuobiServices.get_price_precision('bcxbtc'))
'''

{'status': 'ok', 'data': '1876107434'}
'''
#orderData = HuobiServices.send_order(1,'api','eosusdt','sell-limit',18)
'''
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
'''
#print(orderData)
#print("")
#OrderSendHandle(orderData)

#orderData = HuobiServices.order_info('1876107434')

'''
{'status': 'ok', 'data': {'id': 1876107434, 'symbol': 'eosusdt', 'account-id': 634980, 'amount': '1.000000000000000000', 'price': '18.000000000000000000', 'created-at': 1519710682948, 'type': 'sell-limit', 'field-amount': '0.0', 'field-cash-amount': '0.0', 'field-fees': '0.0', 'finished-at': 0, 'source': 'api', 'state': 'submitted', 'canceled-at': 0}}
'''

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
'''

#OrderInfoHandle(orderData)

#orderData = HuobiServices.cancel_order('1876107434')
#print(orderData)

#orderData = HuobiServices.order_info('1876107434')
#print(orderData)
#OrderInfoHandle(orderData)

#orderData = HuobiServices.send_order(1,'api','xrpusdt','sell-limit',0.9292)
'''
orderData = HuobiServices.order_info('1890939035')
print(orderData)
'''