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
import BalanceManage
import HoldManager
import Const

__tradeOperations = []

class TradeOperation:
    def __init__(self,tradeType,tradePrice,tradeAmount,operationId):
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
        self.exchangerOrderId = ''

    def OrderSended(self,exchangerOrderId):
        """
        当订单成功提交时，更新数据
        """
        self.exchangerOrderId = exchangerOrderId

def SaveTradeOperations():
    pass

def LoadTradeOperations():
    pass

def OnTradeSended(operationId,exchangerOrderId):
    # TODO:
    global __tradeOperations
    for trade in __tradeOperations:
        if trade.operationId == operationId:
            trade.OrderSended(exchangerOrderId)
            break
    SaveTradeOperations()

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
        HoldManager.BuyFilled(trade.operationId, trade.tradePrice,trade.tradeAmount,trade.exchangerOrderId)
    elif tradeOperation.tradeType == 0: # 处理卖出订单成交
        fieldCash = float(fieldCash) - 1 # 这里为避免float交易不精确，所以往少里算一点
        HoldManager.sellFilled(trade.operationId,trade.exchangerOrderId,trade.tradePrice,fieldCash)
        # TODO: 调用BalanceManager操作资金

def SendBuy(operationId, price,amount):
    pass

def SendSell(operationId, price,amount):
    pass

def __WorkThread_CheckTradeFillState():
    """
    检查所有订单的成交状态
    """
    global __tradeOperations
    tradeLen = len(__tradeOperations)
    for x in range(tradeLen - 1, -1, -1):
        trade = __tradeOperations[x]

        if trade.exchangerOrderId != '':
            try:
                jsonResult = HuobiServices.order_info(trade.exchangerOrderId)
                if jsonResult['status'] == 'ok':
                    state = jsonResult['data']['state']
                    if state == 'filled':
                        fieldAmount = jsonResult['data']['field-amount']
                        fieldCashAmount = jsonResult['data']['field-cash-amount']
                        fieldFees = jsonResult['data']['field-fees']
                        logStr = "FILLED! operationId:{} fieldAmount:{} fieldCashAmount:{} field-fees:{}".format(trade.operationId,fieldAmount,fieldCashAmount,fieldFees)
                        Log.Print(logStr)
                        Log.Info(Const.logFile_orderManager,logStr)
                        OnTradeFilled(tradeOperation)
            except Exception as e:
                logStr = "EXCEPTION! Check Order State Faild! operationId:{} Exception:{}".format(trade.operationId,e)
                Log.Print(logStr)
                Log.Info(Const.logFile_orderManager,logStr)
        time.sleep(1)


def __DoCheckTradeFill():
    t = threading.Thread(__WorkThread_CheckTradeFillState)
    t.setDaemon(True)
    t.start()


