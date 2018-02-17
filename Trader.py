# -*- coding: utf-8 -*-

from Huobi.HuobiMarketDataDownloader import HuobiMarketDataDownloader
from Base.BaseMarketStatus import BaseMarketStatus
from Strategies.MultipleMean import MultipleMean
import time

symbol = 'btcusdt'
downloader = HuobiMarketDataDownloader(symbol)
marketStatus = BaseMarketStatus(2,downloader )
#strategy = MultipleMean()

while True:

    print("深度数据状态:",marketStatus.depthDataState)
    print("firstBidPrice, firstAskPrice: ",marketStatus.firstBidPrice,marketStatus.firstAskPrice)
    logStr = ""
    for key in marketStatus.bidsMeanDict:
        logStr += "{}:{}  ".format(key,marketStatus.firstBidPrice - marketStatus.bidsMeanDict[key][-1])
    if len(logStr) > 0:
        print("BidsMean:",logStr)

    logStr = ""
    for key in marketStatus.asksMeanDict:
        logStr += "{}:{}  ".format(key,marketStatus.firstAskPrice - marketStatus.asksMeanDict[key][-1])
    if len(logStr) > 0:
        print("AsksMean:",logStr)
    time.sleep(1)
    pass


# 这里要考虑一下，要不要将将每一次的差价进行平均，以算出差价的趋势

'''
while True:
    downloadResult = downloader.DownloadDepthData()
    # 如果数据下载失败了，等待0.5秒后再试
    if downloadResult is None:
        time.sleep(0.5)
        continue
    
    # 数据超过指定次数获取失败，需要清掉数据，然后等待5秒后再开始逻辑
    if len(downloadResult) == 1:
        marketStatus.ResetData()
        strategy.ResetData()
        time.sleep(5)
        continue
    
    marketStatus.FillPricesData(downloadResult)
    
    if strategy.CanBuy(marketStatus.firstBidPrice, marketStatus.firstAskPrice):
        # TODO: 调用订单操作，下买单
        pass
    
    # 遍历所有持有单，检查哪些可以卖
    
    # 遍历所有下的买卖单，哪些超过了设定时间，撤单
    
    strategy.UpdateStrategyData(marketStatus.realtimeBids, marketStatus.realtimeAsks)

'''