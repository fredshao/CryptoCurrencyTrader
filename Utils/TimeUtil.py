# -*- coding: utf-8 -*-
import pytz
from datetime import datetime
import time


def GetShanghaiTime():
    tz = pytz.timezone('Asia/Shanghai')
    ts = int(time.time())
    dt = datetime.fromtimestamp(ts,tz)
    return datetime(dt.year,dt.month,dt.day,dt.hour,dt.minute,dt.second,dt.microsecond)
