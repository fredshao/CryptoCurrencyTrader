# -*- coding: utf-8 -*-

import json
import sys
import os
import time
from Utils import IOUtil, Log, TimeUtil
from datetime import datetime

__logFile = "./Log/order.log"
__holdBuyFile = './Data/holdBuy'
__localBuyOrdersFile = './Data/localBuyOrders'
__localSellOrdersFile = './Data/localSellOrders'

holdBuys = []

# 购买和出售订单本地存储，先本地下单，然后进行网络下单
# 系统启动的时候，会用所有的本地下单去检查网络下单，进行数据校对
__localBuyOrders = []
__localSellOrders = []

class HoldBuy:
    def __init__(self,orderId,buyTime,buyPrice,buyAmount,filledAmount,finalCost):
        self.orderId = orderId              # 成交的订单Id
        self.buyTime = buyTime            # 购买时间，（不是订单成交时间）
        self.buyPrice = buyPrice            # 当时的买价
        self.buyAmount = buyAmount          # 当时的购买数量 btc
        self.filledAmount = filledAmount    # 最终成交的数量 btc
        self.finalCost = finalCost          # 最终花费 usdt

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
        except Exception as e:
            print("Fatal Error, Load hold buy file faild!",e)
            Log.Info(__logFile,"Fatal Error , Can not load hold buy data!")
            sys.exit()

def __SaveHoldBuys():
    """
    保存持有购买
    """
    global holdBuys
    jsonStr = json.dumps(holdBuys,default=__HoldBuyObj2Json)
    IOUtil.WriteTextToFile(__holdBuyFile,jsonStr)

def __LoadLocal



def SendBuy(buyPrice,buyAmount,operationId):
    # TODO: call exchanger API to send buy order
    Log.Info(__logFile,"Send Buy Order, operationId:{} buyPrice:{} buyAmount:{}".format(operationId,buyPrice,buyAmount))
    currTime = TimeUtil.GetShanghaiTime()
    


"""
holdBuy1 = HoldBuy(100001,datetime.now(),9657,0.12,0.12,1158.84)
holdBuy2 = HoldBuy(100002,datetime.now(),9963,0.03,0.03,298.89)
holdBuys.append(holdBuy1)
holdBuys.append(holdBuy2)

__SaveHoldBuys()

__LoadHoldBuy()

"""