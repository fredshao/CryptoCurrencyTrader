# -*- coding: utf-8 -*-
from Utils import IOUtil
from Utils import TimeUtil
import os


def Print(*args):
    currTime = TimeUtil.GetShanghaiTime()
    print(currTime,':',*args)


def Info(logFilePath, logText):
    """
    日志写入
    """
    date = TimeUtil.GetShanghaiTime()
    pathArray = os.path.splitext(logFilePath)
    realLogFile = "{}_{}_{}_{}{}".format(pathArray[0],date.year,date.month,date.day,pathArray[1])
    logText = date.strftime("%Y-%m-%d %H:%M:%S") + " - [" + logText + "]"
    IOUtil.AppendTextToFile(realLogFile, logText)
