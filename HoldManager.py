# -*- coding: utf-8 -*-
import os
import json
import sys
from Utils import IOUtil,Log,MathUtil,TimeUtil
from datetime import datetime
import Const
import time

__dataFile = "./Data/hold.dat"
__filledDataFile = "./Data/filledHold.dat"

holds = []

class Hold:
    def __init__(self,buyPrice,holdAmount,buyCost,buyTime, buyOrderId):
        self.buyPrice = buyPrice
        self.holdAmount = holdAmount
        self.buyCost = buyCost
        self.buyTime = buyTime
        self.buyOrderId = buyOrderId
        
        # for sell
        self.state = 'hold' # hold: 正在持有, lock: 准备卖出 ,selling: 正在卖出，selled: 已经卖出成交
        self.sellOrderId = ''
        self.sellFilledPrice = -1
        self.profit = -1

        # 临时操作用
        self.operationId = ''

    def __str__(self):
        return "Hold: buyOrderId:{} buyPrice:{} holdAmount:{} buyCost:{} buyTime:{} state:{} sellOrderId:{}".format(self.buyOrderId, self.buyPrice,self.holdAmount,self.buyCost,self.buyTime,self.state,self.sellOrderId)

    def CanSell(self,bidPrice):
        if self.state != 'hold':
            return False

        gainedQuote = self.holdAmount * bidPrice * 0.998
        profit = gainedQuote - self.buyCost
        if profit <= 0:
            return False
        
        profit = MathUtil.GetPrecision(profit,4)
        profitPercentage = (profit / self.buyCost) * 100

        if profitPercentage >= 5.0:
            return True
    
    def LockHold(self):
        """
        要卖的时候，本地调用此方法锁定一个持有
        """
        if self.state != 'hold':
            logStr = "HM - ##### FAILD! hold lock faild! " + self.__str__()
            Log.Print(logStr)
            Log.Info(Const.logFile,logStr)
            return False
        logStr = "HM - SUCCESS! hold lock successful! " + self.__str__()
        Log.Print(logStr)
        Log.Info(Const.logFile,logStr)
        self.state = 'lock'
        return True

    def UnLockHold(self):
        """
        因为一些原因下单失败，需要回滚持有
        """
        logStr = "HM - UnLock Hold: " + self.__str__()
        Log.Print(logStr)
        Log.Info(Const.logFile,logStr)
        self.state = 'hold'

    def HoldOnSelling(self,sellOrderId):
        """
        当卖单下单成功后，调用此方法设置状态
        """
        if self.state != 'lock':
            logStr = "HM - ##### ERROR! hold state error for Sell! " + self.__str__()
            Log.Print(logStr)
            Log.Info(Const.logFile,logStr)
            
        self.state = 'selling'
        self.sellOrderId = sellOrderId

        
    def SellFilled(self,filledPrice,filledCash):
        """
        当卖单成交时，调用此方法进行最终的结算
        """
        self.sellFilledPrice = filledPrice
        gainedQuote = self.holdAmount * filledPrice * 0.998
        profit = gainedQuote - self.buyCost
        profit = MathUtil.GetPrecision(profit,4)
        if profit <= 0:
            logStr = "HM - ##### FATAL ERROR! You are lose Money: !!!! " + self.__str__ + " filledPrice:{} filledCash:{}".format(filledPrice,filledCash)
            Log.Print(logStr)
            Log.Info(Const.logFile,logStr)
            sys.exit()
        self.state = 'selled'
        self.profit = profit
        logStr = "HM - Cool! Sell Filled: buyPrice:{} buyCost:{} holdAmount:{} sellPrice:{} filledCash:{} profit:{}".format(self.buyPrice,self.buyCost,self.holdAmount,self.sellFilledPrice,filledCash,profit)
        Log.Print(logStr)
        Log.Info(Const.logFile,logStr)


def __HoldObj2Json(obj):
    """
    将一个持有对象转为Json字符串
    """
    return {
        "buyOrderId":obj.buyOrderId,
        "buyPrice":obj.buyPrice,
        "holdAmount":obj.holdAmount,
        "buyCost":obj.buyCost,
        "buyTime":obj.buyTime.strftime("%Y-%m-%d %H:%M:%S"),
        "state":obj.state,
        "sellOrderId":obj.sellOrderId,
        "operationId":obj.operationId
    }

def __HoldJson2Obj(jsonData):
    """
    将持有对象字符串转为持有对象
    """
    buyOrderId = jsonData['buyOrderId']
    buyPrice = jsonData['buyPrice']
    holdAmount = jsonData['holdAmount']
    buyCost = jsonData['buyCost']
    buyTime = datetime.strptime(jsonData['buyTime'],"%Y-%m-%d %H:%M:%S")
    state = jsonData['state']
    sellOrderId = jsonData['sellOrderId']
    operationId = jsonData['operationId']

    hold = Hold(buyPrice,holdAmount,buyCost,buyTime,buyOrderId)
    hold.state = state
    hold.sellOrderId = sellOrderId
    hold.operationId = operationId
    return hold

def GetCanSellHolds(bidPrice):
    """
    获取所有可以卖的持有
    """
    canSellHolds = []
    index = 10000
    for hold in holds:
        if hold.CanSell(bidPrice):
            
            if hold.LockHold():
                index += 1
                operationId = str(time.time() + index)
                hold.operationId = (operationId)
                canSellHolds.append(hold)
                #SaveHoldsData()
                #return hold
    if len(canSellHolds) > 0:
        SaveHoldsData()
        return canSellHolds
    return None

def FallbackHold(operationId):
    """
    卖出因为一些原因下单失败，回滚持有
    """
    for hold in holds:
        if hold.operationId == operationId:
            hold.UnLockHold()
            logStr = "HM - ##### Fallback Hold: " + hold.__str__()
            Log.Print(logStr)
            Log.Info(Const.logFile,logStr)
            break
    SaveHoldsData()

def HoldOnSelling(operationId,sellOrderId):
    """
    一个持有，卖出下单成功
    """
    for hold in holds:
        if hold.operationId == operationId:
            hold.HoldOnSelling(sellOrderId)
            logStr = "HM - Hold On Selling: " + hold.__str__()
            Log.Print(logStr)
            Log.Info(Const.logFile,logStr)
            break
    SaveHoldsData()

def SellFilled(operationId, sellOrderId, filledPrice, filledCash):
    """
    一个卖出成交了
    """
    for x in range(len(holds)):
        hold = holds[x]
        if hold.operationId == operationId:
            hold.SellFilled(filledPrice,filledCash)
            del holds[x]
            ArchiveHold(hold)
            logStr = "HM - Sell Filled: " + hold.__str__()
            Log.Print(logStr)
            Log.Info(Const.logFile,logStr)
            break
    SaveHoldsData()

def GetArchiveHoldStr(hold):
    return "buyOrderId:{} buyPrice:{} holdAmount:{} buyCost:{} buyTime:{} sellOrderId:{} sellPrice:{} profit:{}\n".format(hold.buyOrderId,hold.buyPrice,hold.holdAmount,hold.buyCost,hold.buyTime,hold.sellOrderId,hold.sellFilledPrice,hold.profit)

def ArchiveHold(hold):
    """
    将已经卖出成交的持有归档
    """
    archiveStr = GetArchiveHoldStr(hold)
    IOUtil.AppendTextToFile(__filledDataFile,archiveStr)

def BuyFilled(operationId, price, amount,cost, buyOrderId):
    """
    买入成功，创建一个Hold
    """
    #(self,buyPrice,holdAmount,buyCost,buyTime, buyOrderId):
    global holds
    time = TimeUtil.GetShanghaiTime()
    hold = Hold(price,amount,cost,time,buyOrderId)
    
    holds.append(hold)
    SaveHoldsData()

def __LoadHoldsData():
    """
    加载所有的持有数据
    """
    global holds
    if os.path.exists(__dataFile):
        try:
            jsonStr = IOUtil.ReadTextFromFile(__dataFile)
            holds = json.loads(jsonStr,object_hook=__HoldJson2Obj)
        except Exception as e:
            logStr = "HM - ##### EXCEPTION! Load Hold Buy data exception: {}".format(e)
            Log.Print(logStr)
            Log.Info(Const.logFile,logStr)
            sys.exit()

def SaveHoldsData():
    """
    将持有数据保存到文件
    """
    global holds
    jsonStr = json.dumps(holds,default=__HoldObj2Json)
    IOUtil.WriteTextToFile(__dataFile,jsonStr)


def Start():
    __LoadHoldsData()

#__LoadHoldsData()
#MakeHold(10820,0.02,265,TimeUtil.GetShanghaiTime(),'10001434')

#for hold in holds:
    #print(hold)

#hold = GetCanSellHold(11972)
#print("CanSell:\n",hold)