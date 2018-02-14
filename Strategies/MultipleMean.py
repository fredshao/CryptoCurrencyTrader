# -*- coding: utf-8 -*-

class MultipleMean:
    def __init__(self):
        # 30s, 1min(60s), 2min(120s), 4min(240), 8min(480s), 16min(960), 
        # 32min(1920), 64min(3840s), 128min(7680s), 256min(15360s), 512min(30720s)
        self.meanPart = [30,60,120,240,480,960,1920,3840,7680,15360,30720]
        self.ResetData()
        self.precision = 2
        
    def ResetData(self):
        self.bidsMeanDict = {}
        self.asksMeanDict = {}
    
    def __GetPrecision__(self,rawValue,precision):
        """
        返回一个数值的特定精度
        """
        precisionStr = "{:.{}f}".format(precision)
        return float(precisionStr.format(rawValue))
    
    def __GetMeanPartValue__(self,valueList, part):
        """
        从数据列表中截取指定范围的数据，然后计算这些数据的均值
        如果计算条件不满足，则返回-1
        """
        count = len(valueList)
        if data_count == 0:
            return -1
        if count % part == 0:
            value = np.mean(valueList[-part:])
            return self.__GetPrecision__(value, self.precision)
        else:
            return -1
    
    def UpdateStrategyData(self,bids,asks):
        """
        更新策略所需要数据
        """
        for part in self.meanPart:
            bidMean = self.__GetMeanPartValue__(bids, part)
            askMean = self.__GetMeanPartValue__(asks, part)
            if bidMean < 0 or askMean < 0:
                # 数据不足，无法计算
                pass
            else:
                if self.bidsMeanDict.__contains__(part) is False:
                    self.bidsMeanDict[part] = []
                self.bidsMeanDict[part].append(bidMean)
                
                if self.asksMeanDict.__contains__(part) is False:
                    self.asksMeanDict[part] = []
                self.asksMeanDict[part].append(askMean)
    
    def CanBuy(self,firstBidPrice,firstAskPrice):
        """
        是否可以买入
        返回: True 或 False
        """
        pass
    
    def CanSell(self,firstBidPrice,firstAskPrice,tradePrice):
        """
        是否可以卖出
        tradePrice: 当时的买价
        返回: True 或 False
        """
        pass
        