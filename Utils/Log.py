# -*- coding: utf-8 -*-
import IOUtil
import TimeUtil
import os

def Info(logFilePath, logText):
    """
    日志写入
    """
    date = TimeUtil.GetShanghaiTime()
    pathArray = os.path.splitext(logFilePath)
    realLogFile = "{}_{}_{}_{}{}".format(pathArray[0],date.year,date.month,date.day,pathArray[1])
    IOUtil.AppendTextToFile(realLogFile, logText)
