# -*- coding: utf-8 -*-
# 获取行情数据，整理数据

import numpy as np
import time
import threading

class BaseMarketStatus:
    """
    存储实时的价格数据，进行数据分类，然后存储，
    对于不同的数据块，分别存储数据状态，是否合法（超时）
    不同的数据块，使用不同的线程去获取
    """
    def __init__(self, pricePrecision, dataDownloader):
        self.__ResetData__()
        self.precision = pricePrecision
        # 30s, 1min(60s), 2min(120s), 4min(240), 8min(480s), 16min(960), 
        # 32min(1920), 64min(3840s), 128min(7680s), 256min(15360s), 512min(30720s)
        self.meanPart = [30,60,120,240,480,960,1920,3840,7680,15360,30720]
        self.dataDownloader = dataDownloader
        self.__InitDataDownloader__()
        
        # 重置数据时间
        self.__lastDepthDataTime = -1
        
        # 数据状态，未来还会加入更多的状态
        self.depthDataState = -1    # < 0 无法使用

        # 启动数据合法性检查器
        t = threading.Thread(target=self.__DataCheckThread__)
        t.setDaemon(True)
        t.start()



# =========================== 初始化和启动数据下载器 =========================== 
    def __InitDataDownloader__(self):
        """
        初始化数据下载器
        设置各种数据的回调
        """
        self.dataDownloader.SetDepthDataCallback(self.__DepthDataCallback__)
        self.dataDownloader.DoWork()
    
# =========================== 重置数据 ===========================
    def __ResetData__(self):
        """
        初始化(重置)行情数据状态
        """
        # 数据存储器重置
        self.realtimeBids = []
        self.realtimeAsks = []
        self.firstBidPrice = -1
        self.firstAskPrice = -1
        self.bidsMeanDict = {}
        self.asksMeanDict = {}

        # 数据状态重置
        self.depthDataState = -1

        # 数据时间重置
        self.__lastDepthDataTime = -1


    def __GetPrecision__(self,rawValue,precision):
        """
        返回一个数值的特定精度
        """
        precisionStr = '{:.%df}' % precision
        result = float(precisionStr.format(rawValue))
        #print("Precision:",rawValue,precision,precisionStr,result)
        return result

    def __GetMeanPartValue__(self,valueList, part):
        """
        从数据列表中截取指定范围的数据，然后计算这些数据的均值
        如果计算条件不满足，则返回-1
        """
        data_count = len(valueList)
        if data_count == 0:
            return -1
        if data_count % part == 0:
            partValueList = valueList[-part:]
            print("ValueList:",valueList)
            print("PartValueList:",partValueList)
            value = np.mean(partValueList)
            return self.__GetPrecision__(value, self.precision)
        else:
            return -1


# =========================== 数据整理模块 ===========================
    def __UpdateDepthData__(self,prices):
        """
        实时处理深度数据（大约每次1s）
        NOTE: 这里前三个价格的平均数，有疑问，要考虑一下是否合理
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

        # 计算每个时段均值，这里存储每一个时段的，未来如果发现数据冗余，那就只存储一个值，不需要列表
        for part in self.meanPart:
            bidMean = self.__GetMeanPartValue__(self.realtimeBids, part)
            askMean = self.__GetMeanPartValue__(self.realtimeAsks, part)
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



# =========================== 网络数据回调模块 ===========================
    
    def __DepthDataCallback__(self,depthData):
        """
        深度数据下载回调
        """
        #print(depthData)
        self.__lastDepthDataTime = int(time.time())
        self.__UpdateDepthData__(depthData)


# =========================== 数据合法性（时间）检查模块）===========================

    def __DataCheckThread__(self):
        """
        数据合法性检查线程：
            1. 深度数据检查
        """
        while True:
            if self.__lastDepthDataTime > 0:
                currTime = int(time.time())
                diffTime = currTime - self.__lastDepthDataTime
                if diffTime >= 5:
                    print("深度数据超时，无法使用")
                    self.depthDataState = -1
                    self.__ResetData__()
                else:
                    # 深度数据合法
                    self.depthDataState = 0

            time.sleep(1)

    
        