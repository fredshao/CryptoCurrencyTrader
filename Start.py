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


def DoStrategy():
    print("Do Strategy")


if __name__ == '__main__':
    InitSystem()
    StartModules()
    
    while(True):
        DoStrategy()
        time.sleep(1)

    