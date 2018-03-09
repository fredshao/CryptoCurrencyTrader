# -*- coding: utf-8 -*-
import os
import json
import sys
from Utils import IOUtil,Log,MathUtil
import Const

# Buy -> 资金冻结 -> 成交 -> 冻结消耗
#                -> 回滚 -> 冻结回到原始资金

# Sell -> 成交 -> 原始资金 Base 减去卖出数量
#      -> 回滚 -> 无操作 

__baseBalance = 0           # 当前持有的 base 资金(btc)
__quoteBalance = 3000       # 当前持有的可以购买的资金
__frozeQuoteBalance = 0     # 当前冻结的购买资金
__totalProfit = 0           # 盈利累加
__totalQuote = 3000         # 从原始资金加上总盈利的资金
__tradePart = 3

__logFile = "./Log/balance.log"
__balanceFile = './Data/balance'


def __LogBalance(actionName):
    global __baseBalance,__quoteBalance,__frozeQuoteBalance,__totalProfit,__totalQuote
    Log.Print("BM - {}: baseBalance:{} quoteBalance:{} frozeQuote:{} totalProfit:{} totalQuote:{}".format(actionName,__baseBalance,__quoteBalance,__frozeQuoteBalance,__totalProfit,__totalQuote))
    Log.Info(Const.logFile,"BM - {}: baseBalance:{} quoteBalance:{} frozeQuote:{} totalProfit:{} totalQuote:{}".format(actionName,__baseBalance,__quoteBalance,__frozeQuoteBalance,__totalProfit,__totalQuote))

def __LoadBalance():
    """
    加载资产数据，如果数据文件不存在，则初始化资产数据
    """
    global __baseBalance,__quoteBalance,__frozeQuoteBalance,__totalProfit,__totalQuote
    
    if os.path.exists(__balanceFile):
        try:
            jsonStr = IOUtil.ReadTextFromFile(__balanceFile)
            jsonData = json.loads(jsonStr)
            __baseBalance = jsonData['baseBalance']
            __quoteBalance = jsonData['quoteBalance']
            __frozeQuoteBalance = jsonData['frozeQuoteBalance']
            __totalProfit = jsonData['totalProfit']
            __totalQuote = jsonData['totalQuote']
        except Exception as e:
            Log.Print("BM - ##### Fatal Error , can not load balance file! ",e)
            Log.Info(Const.logFile,"BM - ##### Fatal Error, Can not load balance file! " + str(e))
            sys.exit()     
    else:
        __SaveBalance()

def __SaveBalance():
    """
    保存资产数据
    """
    global __baseBalance,__quoteBalance,__frozeQuoteBalance,__totalProfit,__totalQuote
    dictData = {}
    dictData['baseBalance'] = __baseBalance
    dictData['quoteBalance'] = __quoteBalance
    dictData['frozeQuoteBalance'] = __frozeQuoteBalance
    dictData['totalProfit'] = __totalProfit
    dictData['totalQuote'] = __totalQuote
    balanceData = json.dumps(dictData)
    IOUtil.WriteTextToFile(__balanceFile,balanceData)

def Buy(price):
    """
    购买：根据价格和购买单位计算出需要花费多少 quote,把 quote 从原始资金拿到冻结资金中
    注意：这里的价格是已经加了0.3 usdt 后的价格
    """
    global __totalQuote,__tradePart, __quoteBalance,__frozeQuoteBalance
    
    # 计算每次买入多少 usdt 的 btc
    costQuote = MathUtil.GetPrecision(__totalQuote / __tradePart,2)
    if __quoteBalance > costQuote: # 资金足够，可以购买
        __LogBalance("Before Buy Action")
        __quoteBalance -= costQuote
        __frozeQuoteBalance += costQuote

        # 计算要花费的 usdt 按现在的价格能买多少 btc
        buyAmount = costQuote / price
        buyAmount = MathUtil.GetPrecision(buyAmount,4)

        Log.Print("BM - Buy Info: price:{} costQuote:{} buyAmount:{}".format(price,costQuote,buyAmount))
        Log.Info(Const.logFile,"BM - Buy Info: price:{} costQuote:{} buyAmount:{}".format(price,costQuote,buyAmount))

        __SaveBalance()
        __LogBalance("After Buy Action")
        return costQuote, buyAmount  # 返回以 costQuote usdt 买入 buyAmount 的 btc
    return -1,-1

def BuyFilled(costQuote, baseAmount):
    """
    买入成交，从冻结资金中减去当时的花费，然后把购买的 base 数量加到原始资金中
    注意：传到这里的 baseAmount 是已经去掉手续费的了
    """
    global __frozeQuoteBalance,__baseBalance
    __LogBalance("Before Buy Filled")
    Log.Print("BM - Buy Filled Info: costQuote:{} filledAmount:{}".format(costQuote,baseAmount))
    Log.Info(Const.logFile,"BM - Buy Filled Info: costQuote:{} filledAmount:{}".format(costQuote,baseAmount))
    __frozeQuoteBalance -= costQuote
    __baseBalance += baseAmount
    __SaveBalance()
    __LogBalance("After Buy Filled")

def BuyFallback(costQuote):
    """
    购买回滚，把当时要花费的 quote 从冻结资金拿到原始资金
    """
    global __quoteBalance, __frozeQuoteBalance
    __LogBalance("Before Buy Fallback")
    Log.Print("BM - Buy Fallback Info: costQuote:{}".format(costQuote))
    Log.Info(Const.logFile,"BM - Buy Fallback Info: costQuote:{}".format(costQuote))
    __frozeQuoteBalance -= costQuote
    __quoteBalance += costQuote
    __SaveBalance()
    __LogBalance("After Buy Fallback")

def Sell():
    """
    如果是卖出，只是移动了持有买单，不涉及到资金的操作
    """
    pass

def SellFilled(filledQuote,profit,selledAmount):
    """
    如果卖出成交了，则把获得的 quote 资金加到原始资金中
    """
    global __baseBalance,__quoteBalance,__totalQuote,__totalProfit
    __LogBalance("Before Sell Filled")
    Log.Print("BM - Sell Filled Info: filledQuote:{} profit:{} selledAmount:{}".format(filledQuote,profit,selledAmount))
    Log.Info(Const.logFile,"BM - Sell Filled Info: filledQuote:{} profit:{} selledAmount:{}".format(filledQuote,profit,selledAmount))
    __baseBalance -= selledAmount
    __quoteBalance += filledQuote
    __totalProfit += profit
    __totalQuote += profit
    __SaveBalance()
    __LogBalance("After Sell Filled")

def SellFallback():
    """
    卖出回滚，只是移动持有买单，从卖出放回到持有，不需要做其他操作
    """
    pass


def Start():
    __LoadBalance()
