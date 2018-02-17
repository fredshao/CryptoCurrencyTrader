# -*- coding: utf-8 -*-
from Base.BaseMarketDataDownloader import BaseMarketDataDownloader
from API.Huobi import HuobiServices
import time
import threading

class HuobiMarketDataDownloader(BaseMarketDataDownloader):
    """
    火币网深度数据下载器
    返回原始的7个买单和7个卖单
    """
    def __init__(self,symbol):
        self.exchangerName = "Huobi"
        super().__init__(self.exchangerName)
        self.symbol = symbol
        self.exceptionCount = 0

    def SetDepthDataCallback(self,callback):
        """
        设置深度数据下载回调
        """
        self.depthDataCallback = callback
        
    def DoWork(self):
        """
        开始下载数据，不同模块的数据放到不同线程中去下载
        """
        t = threading.Thread(target=self.__WorkThread_DepthData)
        t.setDaemon(True)
        t.start()
        
    def __WorkThread_DepthData(self):
        """
        价格深度数据下线程
        """
        while True:
            dataResult = self.__DownloadDepthData__()
            if dataResult != None and self.depthDataCallback != None:
                self.depthDataCallback(dataResult)
            
    def __DownloadDepthData__(self):
        """
        下载深度数据，用 time.sleep 大概保证每秒返回一个数据，不至于太快导致计算上的复杂
        如果本次获取数据失败，则返回 None
        如果连续10次获取数据失败，则返回 ("ResetData,)的 tuple,上层应该重置趋势数据，重新获取和计算
        """
        try:
            startTime = time.time()
            depthData = HuobiServices.get_depth(self.symbol,'step0')
            bid1 = depthData['tick']['bids'][0][0]
            bid2 = depthData['tick']['bids'][1][0]
            bid3 = depthData['tick']['bids'][2][0]
            bid4 = depthData['tick']['bids'][3][0]
            bid5 = depthData['tick']['bids'][4][0]
            bid6 = depthData['tick']['bids'][5][0]
            bid7 = depthData['tick']['bids'][6][0]

            ask1 = depthData['tick']['asks'][0][0]
            ask2 = depthData['tick']['asks'][1][0]
            ask3 = depthData['tick']['asks'][2][0]
            ask4 = depthData['tick']['asks'][3][0]
            ask5 = depthData['tick']['asks'][4][0]
            ask6 = depthData['tick']['asks'][5][0]
            ask7 = depthData['tick']['asks'][6][0]
            
            endTime = time.time()
            usedTime = endTime - startTime
            waitTime = 1 - usedTime - 0.1
            
            if waitTime > 0:
                time.sleep(waitTime)
                
            return (bid1,bid2,bid3,bid4,bid5,bid6,bid7,ask1,ask2,ask3,ask4,ask5,ask6,ask7)
        except Exception as e:
            print("Download DepthData Exception: ",e)
            time.sleep(2)
            return None
            

'''
def DepthDataCallback(depthData):
    print(depthData)

downloader = HuobiMarketDataDownloader('btcusdt',DepthDataCallback)

while True:
    pass
'''