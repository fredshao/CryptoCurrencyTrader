# -*- coding: utf-8 -*-
from API.Huobi import HuobiServices
from Utils import Log
import threading
import time


realTimeAsks = []
realTimeBids = []

__symbol = 'btcusdt'
__logFile = "./Log/DataDownloader.log"

# 用于临时处理异常的记录变量
__lastExceptionTime = -1
__exceptionCount = 0

__exceptionTime = -1
__exceptionCountIn1Min = 0

__dataTime = -1

def __InitData():
    """
    初始化卖单和买价价存储列表
    """
    global realTimeAsks,realTimeBids
    realTimeAsks = []
    realTimeBids = []

def __ParseData(bid,ask):
    """
    存储卖单和买单的价格
    """
    global realTimeAsks,realTimeBids,__dataTime
    # 进行数据裁剪，不需要存那么多数据
    if len(realTimeAsks) > 3600:
        realTimeAsks = realTimeAsks[-120:]
    if len(realTimeBids) > 3600:
        realTimeBids = realTimeBids[-120:]

    realTimeBids.append(bid)
    realTimeAsks.append(ask)
    __dataTime = int(time.time())
    
def __WorkThread():
    """
    数据下载线程
    如果换成别的交易所，需要改这个函数里的下载那一行代码
    """
    global __exceptionTime,__exceptionCount

    while(True):
        try:
            startTime = time.time()
            
            depthData = HuobiServices.get_depth(__symbol,'step0')

            endTime = time.time()
            usedTime = endTime - startTime
            waitTime = 1 - usedTime - 0.1

            if depthData != None and depthData['status'] == 'ok':
                bid1 = depthData['tick']['bids'][0][0]
                ask1 = depthData['tick']['asks'][0][0]
                __ParseData(bid1,ask1)

            if waitTime > 0:
                time.sleep(waitTime)
        except Exception as e:
            if __exceptionTime < 0:
                __exceptionTime = int(time.time())

            __exceptionCount += 1
            Log.Info(__logFile,"Exception: " + str(e))
            time.sleep(1)
        finally:
            if __exceptionTime > 0:
                currTime = int(time.time())
                diffSeconds = currTime - __exceptionTime
                if diffSeconds >= 60:
                    #print("Exceptioin Count in 1Min:",__exceptionCount)
                    Log.Info(__logFile,"Exception Count in 1Min: {}".format(__exceptionCount))

                    if __exceptionCount > 10:
                        Log.Info(__logFile,"more than 15 times Exception in 1Min, Clear Data")
                        __InitData()

                    __exceptionTime = currTime
                    __exceptionCount = 0


def DataValid():
    """
    如果上一次更新数据超过了10s，则视为数据不合法，使用数据前，要检查数据的合法性
    """
    currTime = int(time.time())
    if __dataTime > 0 and currTime - __dataTime < 10:
        return True

    return False


def Start():
    t = threading.Thread(target=__WorkThread)
    t.setDaemon(True)
    t.start()
    print("DataDownloader Started!")


'''
Start()

while(True):
    pass

'''