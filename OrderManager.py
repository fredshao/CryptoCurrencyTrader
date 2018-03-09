# -*- coding: utf-8 -*-
"""
这个模块的功能是，下买卖单，若成功，则记录，失败则资金回滚
"""

import json
import sys
import os
import time
from Utils import IOUtil, Log, TimeUtil,MathUtil
from datetime import datetime
import threading
from API.Huobi import HuobiServices
import BalanceManager
import HoldManager
import Const

__tradeOperations = []

__terminated = False

class TradeOperation:
    def __init__(self,tradeType,tradePrice,tradeAmount,operationId, exchangerOrderId,cost = -1):
        """
        tradeType: 0 卖出，1 买入
        tradePrice: 交易限价单价格
        tradeAmount: 交易数量
        operationId: 交易操作标识
        exchangerOrderId: 交易所订单Id
        """
        self.tradeType = tradeType
        self.tradePrice = tradePrice
        self.tradeAmount = tradeAmount
        self.operationId = operationId
        self.exchangerOrderId = exchangerOrderId
        self.cost = cost

    def OrderSended(self,exchangerOrderId):
        """
        当订单成功提交时，更新数据
        """
        self.exchangerOrderId = exchangerOrderId

def __TradeOperation2Json(obj):
    return {
        "tradeType":obj.tradeType,
        "tradePrice":obj.tradePrice,
        "tradeAmount":obj.tradeAmount,
        "operationId":obj.operationId,
        "cost":obj.cost,
        "exchangerOrderId":obj.exchangerOrderId
        
    }

def __Json2TradeOperationObj(jsonData):
    tradeType = jsonData['tradeType']
    tradePrice = jsonData['tradePrice']
    tradeAmount = jsonData['tradeAmount']
    operationId = jsonData['operationId']
    cost = jsonData['cost']
    exchangerOrderId = jsonData['exchangerOrderId']
    operation = TradeOperation(tradeType,tradePrice,tradeAmount,operationId, exchangerOrderId, cost)
    return operation

def SaveTradeOperations():
    global __tradeOperations
    jsonStr = json.dumps(__tradeOperations,default=__TradeOperation2Json)
    IOUtil.WriteTextToFile(Const.dataFile_orderManager,jsonStr)

def LoadTradeOperations():
    global __tradeOperations
    if os.path.exists(Const.dataFile_orderManager):
        try:
            jsonStr = IOUtil.ReadTextFromFile(Const.dataFile_orderManager)
            __tradeOperations = json.loads(jsonStr,object_hook=__Json2TradeOperationObj)
        except Exception as e:
            logStr = "OM - ##### EXCEPTION! Load Trade Operations Faild! EXCEPTION:{}".format(e)
            Log.Print(logStr)
            Log.Info(Const.logFile,logStr)
            sys.exit()


def OnTradeFilled(tradeOperation, fieldCash):
    """
    当一个订单成交时，从操作列表中找到对应的交易索引，然后从交易列表中删除，保存数据
    """
    global __tradeOperations
    index = -1
    for x in range(len(__tradeOperations)):
        trade = __tradeOperations[x]
        if trade.operationId == tradeOperation.operationId:
            index = x
            break

    if index >= 0:
        del __tradeOperations[index]

    SaveTradeOperations()

    if tradeOperation.tradeType == 1: # 处理买入订单成交
        gainedBase = tradeOperation.tradeAmount * 0.997
        gainedBase = MathUtil.GetPrecision(gainedBase,4)
        logStr = "OM - Buy Order Filled: operationId:{} gainedBase:{}".format(tradeOperation.operationId,gainedBase)
        Log.Print(logStr)
        Log.Info(Const.logFile,logStr)
        HoldManager.BuyFilled(tradeOperation.operationId, tradeOperation.tradePrice,gainedBase, tradeOperation.cost, tradeOperation.exchangerOrderId)
        BalanceManager.BuyFilled(tradeOperation.cost,gainedBase)
    elif tradeOperation.tradeType == 0: # 处理卖出订单成交
        # TODO: 这里要实际成交一单，查看一下最终收益和自己计算的收益是否一样
        fieldCash = float(fieldCash) * 0.997 # 这里为避免float交易不精确，所以往少里算一点
        profit = fieldCash - tradeOperation.cost
        logStr = "OM - Sell Order Filled: operationId:{} fieldCash:{} profit:{}".format(tradeOperation.operationId,fieldCash,profit) 
        Log.Print(logStr)
        Log.Info(Const.logFile,logStr)
        HoldManager.SellFilled(tradeOperation.operationId,tradeOperation.exchangerOrderId,tradeOperation.tradePrice,fieldCash)
        BalanceManager.SellFilled(fieldCash,profit,tradeOperation.tradeAmount)


def SendBuy(operationId, price, amount, cost):
    """
    直接在主线程中下买单，最多尝试2次
    买入下单
    operationId: 操作Id
    price: 买入价格
    amount: 买入数量
    cost: 买入总花费
    """
    global __tradeOperations
    for x in range(2):
        orderSended = False
        try:
            #orderData = HuobiServices.send_order(amount,'api','btcusdt','buy-limit',price)
            orderData = __DEBUG_ConstructTradeResult()
            status = orderData['status']
            orderId = orderData['data']
            if status == 'ok':
                orderSended = True
                buyOperation = TradeOperation(1,price,amount,operationId,orderId, cost)
                __tradeOperations.append(buyOperation)
                SaveTradeOperations()
                logStr = "OM - SUCCESS! Send Buy Order OK! operationId:{} price:{} amount:{} cost:{} orderId:{}".format(operationId,price,amount,cost,orderId)
                Log.Print(logStr)
                Log.Info(Const.logFile, logStr)
                return
            else:
                logStr = "OM - ##### FAILD! Send Buy Order FAILD! operationId:{} price:{} amount:{} rawJson:{}".format(operationId,price,amount,orderData)
                Log.Print(logStr)
                Log.Info(Const.logFile,logStr)
        except Exception as e:
            logStr = "OM - ##### EXCEPTION! Send Buy Order Exception! operationId:{} price:{} amount:{} Exception:{}".format(operationId,price,amount,e)
            Log.Print(logStr)
            Log.Info(Const.logFile,logStr)

            if orderSended == True:
                logStr = "OM - #### Buy FATAL ERROR!!!!!"
                Log.Print(logStr)
                Log.Info(Const.logFile,logStr)

            time.sleep(1)

    #走到这里，说明下买单失败，资金回滚
    BalanceManage.BuyFallback(cost)

def SendSell(operationId,price,amount, buyCost):
    """
    卖出持有
    operationId: 操作Id 
    price: 卖出价格
    amount: 卖出数量
    buyCost: 购买的时候花了多少钱，用于计算收益
    """
    global __tradeOperations
    for x in range(2):
        orderSended = False
        try:
            #orderData = HuobiServices.send_order(amount,'api','btcusdt','sell-limit',price)
            orderData = __DEBUG_ConstructTradeResult()
            status = orderData['status']
            orderId = orderData['data']
            if status == 'ok':
                orderSended = True
                sellOperation = TradeOperation(0,price,amount,operationId,orderId, buyCost)
                __tradeOperations.append(sellOperation)
                SaveTradeOperations()
                logStr = "OM - SUCCESS! Send Sell Order OK! operationId:{} price:{} amount:{} cost:{} orderId:{}".format(operationId,price,amount,buyCost,orderId)
                Log.Print(logStr)
                Log.Info(Const.logFile,logStr)
                return
            else:
                logStr = "OM - ##### FAILD! Send Sell Order FAILD! operationId:{} price:{} amount:{} rawJson:{}".format(operationId,price,amount,orderData)
                Log.Print(logStr)
                Log.Info(Const.logFile,logStr)
        except Exception as e:
            logStr = "OM - ##### EXCEPTION! Send Sell Order Exception! operationId:{} price:{} amount:{} Exception:{}".format(operationId,price,amount,e)
            Log.Print(logStr)
            Log.Info(Const.logFile,logStr)

            if orderSended == True:
                logStr = "OM - #### Sell FATAL ERROR!!!!!"
                Log.Print(logStr)
                Log.Info(Const.logFile,logStr)
                sys.exit()

            time.sleep(1)
    # 因为一些原因，卖出失败了，所以要回滚持有
    print("Ready Fallback ",operationId)
    HoldManager.FallbackHold(operationId)

def __WorkThread_CheckTradeFillState():
    """
    检查所有订单的成交状态
    """
    Log.Print("OrderManager Started!")
    global __tradeOperations, __terminated
    while (__terminated != True):
        tradeLen = len(__tradeOperations)
        for x in range(tradeLen - 1, -1, -1):
            trade = __tradeOperations[x]

            if trade.exchangerOrderId != '':
                try:
                    #jsonResult = HuobiServices.order_info(trade.exchangerOrderId)
                    if trade.tradeType == 1:
                        jsonResult = __DEBUG_ConstructBuyFillResult(trade.tradePrice,trade.tradeAmount)
                    else:
                        jsonResult = __DEBUG_ConstructSellFillResult(trade.tradePrice,trade.tradeAmount)
                        
                    if jsonResult['status'] == 'ok':
                        state = jsonResult['data']['state']
                        if state == 'filled':
                            fieldAmount = jsonResult['data']['field-amount']
                            fieldCashAmount = jsonResult['data']['field-cash-amount']
                            fieldFees = jsonResult['data']['field-fees']
                            logStr = "OM - Exchanger Order FILLED! operationId:{} fieldAmount:{} fieldCashAmount:{} field-fees:{}".format(trade.operationId,fieldAmount,fieldCashAmount,fieldFees)
                            Log.Print(logStr)
                            Log.Info(Const.logFile,logStr)
                            OnTradeFilled(trade,fieldCashAmount)
                except Exception as e:
                    logStr = "OM - ##### EXCEPTION! Check Order State Faild! operationId:{} Exception:{}".format(trade.operationId,e)
                    Log.Print(logStr)
                    Log.Info(Const.logFile,logStr)
            time.sleep(1)
        time.sleep(2)
    Log.Print("!!!Terminated OrderManager Stoped!")

def __DoCheckTradeFill():
    t = threading.Thread(target=__WorkThread_CheckTradeFillState)
    t.setDaemon(True)
    t.start()


def Start():
    LoadTradeOperations()
    __DoCheckTradeFill()

def Stop():
    global __terminated
    __terminated = True




def __DEBUG_ConstructTradeResult():
    orderId = str(int(time.time() * 10000))
    rStr = '{"status": "ok", "data": "%s"}' % (orderId)
    return json.loads(rStr)


def __DEBUG_ConstructBuyFillResult(price,amount):
    rStr = '{"status": "ok", "data": {"id": 1876107434, "symbol": "btcusdt", "account-id": 634980, "amount": "%f", "price": "%f", "created-at": 1519710682948, "type": "buy-limit", "field-amount": "%f", "field-cash-amount": "%f", "field-fees": "0.0", "finished-at": 0, "source": "api", "state": "filled", "canceled-at": 0}}' % (amount,price,amount,price * amount)
    return json.loads(rStr)

def __DEBUG_ConstructSellFillResult(price,amount):
    rStr = '{"status": "ok", "data": {"id": 1876107434, "symbol": "btcusdt", "account-id": 634980, "amount": "%f", "price": "%f", "created-at": 1519710682948, "type": "sell-limit", "field-amount": "%f", "field-cash-amount": "%f", "field-fees": "0.0", "finished-at": 0, "source": "api", "state": "filled", "canceled-at": 0}}' % (amount,price,amount,price * amount)
    return json.loads(rStr)
    
#orderData = __DEBUG_ConstructTradeResult()
#print(orderData['status'])

#print(__DEBUG_ConstructTradeResult())
#print(__DEBUG_ConstructSellFillResult(9987,0.1))

#orderData = __DEBUG_ConstructBuyFillResult(8091,0.1)
#print(orderData['status'],orderData['data']['state'])