# -*- coding: utf-8 -*-
# 从交易所获取最原始的数据

class BaseMarketDataDownloader:
    def __init__(self,exchangerName):
        self.exchangerName = exchangerName
        
    def DwonloadDepthData(self):
        print("haha")