# -*- coding: utf-8 -*-
from Base.BaseMarketDataDownloader import BaseMarketDataDownloader
from API.Huobi import HuobiServices
import time

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
        
        
    def DownloadDepthData(self):
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
            
            self.exceptionCount = 0
            
            endTime = time.time()
            usedTime = endTime - startTime
            waitTime = 1 - usedTime - 0.1
            
            if waitTime > 0:
                time.sleep(waitTime)
                
            return (bid1,bid2,bid3,bid4,bid5,bid6,bid7,ask1,ask2,ask3,ask4,ask5,ask6,ask7)
        except Exception as e:
            self.exceptionCount += 1
            print("Download DepthData Exception: ",e)
            if self.exceptionCount >= 10:
                # 告诉上层，清掉行情数据 ，因为行情数据延迟了有几秒了
                return ("ResetData",)
            else:
                return None
            
'''
# Do Test
downloader = HuobiMarketDataDownloader("Huobi",'btcusdt')
for x in range(100):
    print(downloader.DownloadDepthData())
'''