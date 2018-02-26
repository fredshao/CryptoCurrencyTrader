# -*- coding: utf-8 -*-

import DataDownloader
import BalanceManager
import time

def RecoverSystem():
    pass

def StartSystem():
    RecoverSystem()
    DataDownloader.Start()
    BalanceManager.Start()


def DoStrategy():
    print("Do Strategy")


if __name__ == '__main__':
    InitSystem()
    StartModules()
    
    while(True):
        DoStrategy()
        time.sleep(1)

    