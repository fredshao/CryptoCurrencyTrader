# -*- coding: utf-8 -*-
from API.Huobi import HuobiServices
from Utils import Log
import threading
import time


realTimeAsks = []
realTimeBids = []

__symbol = 'btcusdt'
__logFileName = "./Log/DataDownloader.log"

# 用于临时处理异常的记录变量
__lastExceptionTime = -1
__exceptionCount = 0

__exceptionTime = -1
__exceptionCountIn1Min = 0


def __InitData():
    global realTimeAsks,realTimeBids
    realTimeAsks = []
    realTimeBids = []

def __ParseData(bid,ask):
    global realTimeAsks,realTimeBids
    # 进行数据裁剪，不需要存那么多数据
    if len(realTimeAsks) > 3600:
        realTimeAsks = realTimeAsks[-120:]
    if len(realTimeBids) > 3600:
        realTimeBids = realTimeBids[-120:]

    realTimeBids.append(bid)
    realTimeAsks.append(ask)
    print(bid,ask)
    
def __WorkThread():
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
            Log.Info(__logFileName,"Exception: " + str(e))
        finally:
            if __exceptionTime > 0:
                currTime = int(time.time())
                diffSeconds = currTime - __exceptionTime
                if diffSeconds >= 60:
                    #print("Exceptioin Count in 1Min:",__exceptionCount)
                    Log.Info(__logFileName,"Exception Count in 1Min: {}".format(__exceptionCount))

                    if __exceptionCount > 10:
                        Log.Info(__logFileName,"more than 15 times Exception in 1Min, Clear Data")
                        __InitData()

                    __exceptionTime = currTime
                    __exceptionCount = 0


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