# -*- coding: utf-8 -*-
# 从交易所获取最原始的数据

class BaseMarketDataDownloader:
    """
    抽象数据下载器
    按设定的频率，在子线程中不断获取数据
    采用数据回调，将数据传入上层
    不同的数据模块最好全用不同的线程
    """
    def __init__(self,exchangerName):
        self.exchangerName = exchangerName
        
    def DwonloadDepthData(self):
        print("haha")