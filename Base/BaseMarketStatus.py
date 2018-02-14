# -*- coding: utf-8 -*-
# 获取行情数据，整理数据

import numpy as np

class BaseMarketStatus:
    """
    存储实时的价格数据
    """
    def __init__(self):
        self.ResetData()
        self.precision = 2
    
    def ResetData(self):
        """
        初始化(重置)行情数据状态
        """
        self.realtimeBids = []
        self.realtimeAsks = []
        self.firstBidPrice = 0.0
        self.firstAskPrice = 0.0

    def __GetPrecision__(self,rawValue,precision):
        """
        返回一个数值的特定精度
        """
        precisionStr = "{:.{}f}".format(precision)
        return float(precisionStr.format(rawValue))
    
    def FillPricesData(self,prices):
        """
        实时(大约1s每次)填充买价和卖价数据
        """
        bid1 = prices[0]
        bid2 = prices[1]
        bid3 = prices[2]
        bidMean = self.__GetPrecision__(np.mean([bid1,bid2,bid3]), self.precision)
        self.realtimeBids.append(bidMean)
        
        ask1 = prices[7]
        ask2 = prices[8]
        ask3 = prices[9]
        askMean = self.__GetPrecision__(np.mean([ask1,ask2,ask3]), self.precision) 
        self.realtimeAsks.append(askMean)
        
        self.firstBidPrice = bid1
        self.firstAskPrice = ask1
        