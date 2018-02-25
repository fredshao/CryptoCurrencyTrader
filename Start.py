# -*- coding: utf-8 -*-

import DataDownloader

import time

def InitSystem():
    """
    系统初始化，加载所有数据
    """
    pass



def StartModules():
    DataDownloader.Start()


StartModules()


while(True):
    print(len(DataDownloader.realTimeBids),len(DataDownloader.realTimeAsks))
    time.sleep(1)
    