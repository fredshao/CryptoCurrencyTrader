# -*- coding: utf-8 -*-

persions = {}
import time

def WorkThread(price,amount,operationId):
    print(price,amount,operationId)


import threading

t = threading.Thread(target=WorkThread,args=(11011.12,0.02,str(time.time())))
t.start()

while(True):
    pass

