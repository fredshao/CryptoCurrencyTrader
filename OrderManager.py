# -*- coding: utf-8 -*-

import json
import sys
import os
import time
from Utils import IOUtil, Log, TimeUtil
from datetime import datetime
import threading
from AIP.Huobi import HuobiServices

SYMBOL = 'btcusdt'

__logFile = "./Log/order.log"
__holdBuyFile = './Data/holdBuy'
__localBuyOrdersFile = './Data/localBuyOrders'
__localSellOrdersFile = './Data/localSellOrders'

holdBuys = []

terminated = False

# 购买和出售订单本地存储，先本地下单，然后进行网络下单
# 系统启动的时候，会用所有的本地下单去检查网络下单，进行数据校对
__localBuyOperations = {}
__localSellOperations = {}

# 已经归档案的订单
__archivedOrders = {}

class HoldBuy:
    def __init__(self,orderId,buyTime,buyPrice,buyAmount,filledAmount,finalCost):
        self.orderId = orderId              # 成交的订单Id
        self.buyTime = buyTime            # 购买时间，（不是订单成交时间）
        self.buyPrice = buyPrice            # 当时的买价
        self.buyAmount = buyAmount          # 当时的购买数量 btc
        self.filledAmount = filledAmount    # 最终成交的数量 btc
        self.finalCost = finalCost          # 最终花费 usdt

    def __str__(self):
        return "HoldBuy: orderId:{} buyTime:{} buyPrice:{} buyAmount:{} filledAmount:{} finalCost:{}".format(self.orderId,self.buyTime,self.buyPrice,self.buyAmount,self.filledAmount,self.finalCost)

class OrderOperation:
    def __init__(self,orderType,orderTime,price,amount,operationId):
        """
        orderType: 订单类型，0 卖出，1 买入
        price: 订单价格
        amount: 操作数量
        operationId: 操作ID标识
        """
        self.orderType = orderType
        self.orderTime = orderTime
        self.price = price
        self.amount = amount
        self.operationId = operationId

    def __str__(self):
        return "OrderOperation: orderType:{} orderTime:{} price:{} amount:{} operationId:{}".format(self.orderType,self.orderTime,self.price,self.amount,self.operationId)


class ExchangerOrderOperation:
    def __init__(self,orderType,price,amount,operationId,exchangerOrder = None):
        self.orderType = orderType
        self.price = price
        self.amount = amount
        self.operationId = operationId
        self.exchangerOrder = exchangerOrder
        self.__DoIt()

    def __OrderThread(self):
        print("Hello:{} {} {} {}".format(self.orderType,self.price,self.amount,self.operationId))

        # 如果第一次下单失败了，就再尝试一次，一共尝试2次
        # 下单有几种情况，1 超时，2 失败，3 成功
        for x in range(2):
            if self.orderType == 0: # 下卖单
                HuobiServices.send_order(ACCOUNT_ID,self.amount,'api',SYMBOL,'sell-limit',self.price)
            else if self.orderType == 1: # 下买单
                pass

    def __CheckThread(self):
        global terminated
        while True:   # 如果系统未退出
            if terminated == True:
                break

            if self.exchangerOrder != None:
                pass
                # check the order status

                # if the order is filled, archiving the order
            time.sleep(2)

            
    


    def __DoIt(self):
        if self.exchangerOrder == None:
            t = threading.Thread(target=self.__WorkThread)
            t.setDaemon(True)
            t.start()
        
        t1 = threading.Thread(target=self.__CheckThread)
        t1.setDaemon(True)
        t1.start()


def __HoldBuyObj2Json(obj):
    """
    将HoldBuy转为Json字符串
    """
    return {
        "orderId":obj.orderId,
        "buyTime":obj.buyTime.strftime("%Y-%m-%d %H:%M:%S"),
        "buyPrice":obj.buyPrice,
        "buyAmount":obj.buyAmount,
        "filledAmount":obj.filledAmount,
        "finalCost":obj.finalCost
    }

def __HoldBuyJson2Obj(jsonData):
    """
    Json字符串解析为HoldBuy类对象
    """
    orderId = jsonData['orderId']
    buyTime = datetime.strptime(jsonData['buyTime'],"%Y-%m-%d %H:%M:%S")
    buyPrice = jsonData['buyPrice']
    buyAmount = jsonData['buyAmount']
    filledAmount = jsonData['filledAmount']
    finalCost = jsonData['finalCost']
    return HoldBuy(orderId,buyTime,buyPrice,buyAmount,filledAmount,finalCost)

def __OrderOperation2Json(obj):
    """
    将订单操作转为Json字符串
    """
    return {
        "orderType":obj.orderType,
        "orderTime":obj.orderTime.strftime("%Y-%m-%d %H:%M:%S"),
        "price":obj.price,
        "amount":obj.amount,
        "operationId":obj.operationId
    }

def __OrderOperationJson2Obj(jsonData):
    """
    将Json字符串转为OrderOperation类对象
    """

    if len(jsonData) == 0:
        return {}

    if isinstance(jsonData,dict):
        for key in jsonData:
            item = jsonData[key]
            if isinstance(item,OrderOperation):
                return jsonData

    orderType = jsonData['orderType']
    orderTime = datetime.strptime(jsonData['orderTime'],"%Y-%m-%d %H:%M:%S")
    price = jsonData['price']
    amount = jsonData['amount']
    operationId = jsonData['operationId']
    return OrderOperation(orderType,orderTime,price,amount,operationId)    

def __LoadHoldBuy():
    """
    加载持有购买
    """
    global holdBuys
    if os.path.exists(__holdBuyFile):
        try:
            jsonStr = IOUtil.ReadTextFromFile(__holdBuyFile)
            holdBuys = json.loads(jsonStr,object_hook=__HoldBuyJson2Obj)
            print("HoldBuys Loaded:")
            for item in holdBuys:
                print(item)
            print("")
        except Exception as e:
            Log.Print("Fatal Error, Load hold buy file faild!",e)
            Log.Info(__logFile,"Fatal Error , Can not load hold buy data!")
            sys.exit()

def __SaveHoldBuys():
    """
    保存持有购买
    """
    global holdBuys
    jsonStr = json.dumps(holdBuys,default=__HoldBuyObj2Json)
    IOUtil.WriteTextToFile(__holdBuyFile,jsonStr)

def __LoadLocalOperations(fileName):
    """
    加载本地的订单操作
    """
    if os.path.exists(fileName):
        try:
            jsonStr = IOUtil.ReadTextFromFile(fileName)
            localOperations = json.loads(jsonStr,object_hook=__OrderOperationJson2Obj)
            return localOperations
        except Exception as e:
            Log.Print("Fatal Error, Load local operation faild! ",e,fileName)
            Log.Info(__logFile,"Fatal Error, Can not load local operation! " + fileName)
            sys.exit()

    return []

def __SaveLocalOperations(operations, fileName):
    """
    将本地订单操作保存到文件
    """
    jsonStr = json.dumps(operations,default=__OrderOperation2Json)
    IOUtil.WriteTextToFile(fileName,jsonStr)

def __LoadLocalBuyOperations():
    """
    加载本地购买订单操作
    """
    global __localBuyOperations
    __localBuyOperations = __LoadLocalOperations(__localBuyOrdersFile)
    print("Local Buy Operations Loaded:")
    for key in __localBuyOperations:
        print(__localBuyOperations[key])
    print("")

def __SaveLocalBuyOperations():
    """
    保存本地购买订单操作
    """
    global __localBuyOperations
    __SaveLocalOperations(__localBuyOperations,__localBuyOrdersFile)


def __LoadLocalSellOperations():
    """
    加载本地卖出订单操作
    """
    global __localSellOperations
    __localSellOperations = __LoadLocalOperations(__localSellOrdersFile)
    print("Local Sell Operations Loaded:")
    for key in __localSellOperations:
        print(__localSellOperations[key])
    print("")

def __SaveLocalSellOperations():
    """
    保存本地卖出订单操作
    """
    global __localSellOperations
    __SaveLocalOperations(__localSellOperations,__localSellOrdersFile)


def __SendLocalBuy(buyPrice,buyAmount,operationId):
    # 先本地下单
    global __localBuyOperations
    currTime = TimeUtil.GetShanghaiTime()
    buyOperation = OrderOperation(1,currTime,buyPrice,buyAmount,operationId)
    if __localBuyOperations.__contains__(operationId) == False:
        __localBuyOperations[operationId] = buyOperation
        Log.Print("Send local Buy: time:{} operationId:{} buyPrice:{} buyAmount:{}".format(currTime,operationId,buyPrice,buyAmount))
        Log.Info(__logFile,"Send Local Buy: time:{} operationId:{} buyPrice:{} buyAmount:{}".format(currTime,operationId,buyPrice,buyAmount))
        __SaveLocalBuyOperations()
        return True
    else:
        Log.Print("ERROR: Send local buy operation faild, already has operation:{}".format(operationId))
        Log.Info(__logFile,"ERROR: Send local buy operation faild, already has operation:{}".format(operationId))
    return False

def __SendLocalSell(sellPrice,sellAmount,operationId):
    # 下本地卖单
    global __localSellOperations
    currTime = TimeUtil.GetShanghaiTime()
    sellOperation = OrderOperation(0,currTime,sellPrice,sellAmount,operationId)
    if __localSellOperations.__contains__(operationId) == False:
        __localSellOperations[operationId] = sellOperation
        Log.Print("Send Local Sell: time:{} operationId:{} sellPrice:{} sellAmount:{}".format(currTime,operationId,sellPrice,sellAmount))
        Log.Info(__logFile,"Send Local Sell: time:{} operationId:{} sellPrice:{} sellAmount:{}".format(currTime,operationId,sellPrice,sellAmount))
        __SaveLocalSellOperations()
        return True
    else:
        Log.Print("ERROR: Send local sell operation faild, already has operation:{}".format(operationId))
        Log.Info(__logFile,"ERROR: Send local sell operation faild, already has operation:{}".format(operationId))
    return False

def __SendExchangerBuy(buyPrice,buyAmount,operationId):
    """
    与交易所通信，下买单
    """
    Log.Print("Send Exchanger Buy: operationId:{} buyPrice:{} buyAmount:{}".format(operationId,buyPrice,buyAmount))

def __SendExchangerSell(sellPrice,sellAmount,operationId):
    """
    与交易所通信，下卖单
    """
    Log.Print("Send Exchanger Sell: operationId:{} sellPrice:{} sellAmount:{}".format(operationId,sellPrice,sellAmount))

def __ProofreadData():
    pass


def SendBuy(buyPrice,buyAmount,operationId):
    # TODO: call exchanger API to send buy order
    if __SendLocalBuy(buyPrice,buyAmount,operationId) == True:
        __SendExchangerBuy(buyPrice,buyAmount,operationId)

def SendSell(sellPrice,sellAmount,operationId):
    if __SendLocalSell(sellPrice,sellAmount,operationId) == True:
        __SendExchangerSell(sellPrice,sellAmount,operationId)
    

'''
def Start():
    __LoadHoldBuy()
    __LoadLocalBuyOperations()
    __LoadLocalSellOperations()
    __ProofreadData()
'''


#operation = ExchangerOrderOperation(0,11011,0.11,str(time.time()))

#time.sleep(5)


