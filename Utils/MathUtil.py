# -*- coding: utf-8 -*-
from decimal import Decimal

def GetPrecision(value,precision):
    if precision <= 0:
        return int(float(value))

    if precision > 20:
        tmpPrecision = precision + 10
    else:
        tmpPrecision = 20

    value = float(value)
    decimalStr = '0.' + '0' * tmpPrecision
    valueStr = str(Decimal(value).quantize(Decimal(decimalStr)))

    valueArray = valueStr.split('.')
    integerPart = valueArray[0]
    decimalPart = valueArray[1][0:precision]
    resultValueStr = integerPart + "." + decimalPart
    resultValue = float(resultValueStr)

    return resultValue

