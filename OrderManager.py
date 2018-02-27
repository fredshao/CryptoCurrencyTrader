# -*- coding: utf-8 -*-

import json
import sys
import os
import time
from Utils import IOUtil, Log, TimeUtil
from datetime import datetime
import threading
from AIP.Huobi import HuobiServices
import BalanceManager

SYMBOL = 'btcusdt'

__logFile = "./Log/order.log"
__holdBuyFile = './Data/holdBuy'
__localBuyOrdersFile = './Data/localBuyOrders'
__localSellOrdersFile = './Data/localSellOrders'
__exchangerBuyOrdersFile = './Data/exchangerBuyOrders'
__exchangerSellOrdersFile = './Data/exchangerSellOrders'
__sellingHoldBuyFile = './Data/sellingHoldBuy'

terminated = False
holdBuys = []

# 正在卖出中的持有 {"operationId":HoldBuy}
__sellingHoldBuys = {}

# 购买和出售订单本地存储，先本地下单，然后进行网络下单
# 系统启动的时候，会用所有的本地下单去检查网络下单，进行数据校对
__localBuyOperations = {}
__localSellOperations = {}

__exchangerBuyOperations = {}
__exchangerSellOperations = {}

# 已经归档案的订单
__archivedOrders = {}

class HoldBuy:
    def __init__(self,orderId,buyTime,buyPrice,buyAmount,filledAmount,finalCost):
        self.orderId = orderId              # 成交的订单Id
        self.buyTime = buyTime            # 购买时间，（不是订单成交时间）
        self.buyPrice = buyPrice            # 当时的买价
        self.buyAmount = buyAmount          # 当时的购买数量 btc
        self.filledAmount = filledAmount    # 最终成交的数量 btc
        self.finalCost = finalCost          # 最终花费 usdt

    def __str__(self):
        return "HoldBuy: orderId:{} buyTime:{} buyPrice:{} buyAmount:{} filledAmount:{} finalCost:{}".format(self.orderId,self.buyTime,self.buyPrice,self.buyAmount,self.filledAmount,self.finalCost)

class OrderOperation:
    def __init__(self,orderType,orderTime,price,amount,operationId):
        """
        orderType: 订单类型，0 卖出，1 买入
        price: 订单价格
        amount: 操作数量
        operationId: 操作ID标识
        """
        self.orderType = orderType
        self.orderTime = orderTime
        self.price = price
        self.amount = amount
        self.operationId = operationId

    def __str__(self):
        return "OrderOperation: orderType:{} orderTime:{} price:{} amount:{} operationId:{}".format(self.orderType,self.orderTime,self.price,self.amount,self.operationId)


class ExchangerOrderOperation:
    def __init__(self,orderId,orderType,orderTime,price,amount,operationId,state=''):
        """
        orderId: 交易所订单号
        orderType: 0 卖出，1 买入
        price: 操作价格
        amount: 操作数量
        operationId: 操作ID标识
        """
        self.orderId = orderId
        self.orderType = orderType
        self.orderTime = orderTime
        self.price = price
        self.amount = amount
        self.operationId = operationId
        self.state = state

    def __str__(self):
        return "ExchangerOperation: orderId:{} orderType:{} orderTime:{} price:{} amount:{} operationId:{} state:{}".format(self.orderId,self.orderType,self.orderTime,self.price,self.amount,self.operationId,self.state)


def __HoldBuyObj2Json(obj):
    """
    将HoldBuy转为Json字符串
    """
    return {
        "orderId":obj.orderId,
        "buyTime":obj.buyTime.strftime("%Y-%m-%d %H:%M:%S"),
        "buyPrice":obj.buyPrice,
        "buyAmount":obj.buyAmount,
        "filledAmount":obj.filledAmount,
        "finalCost":obj.finalCost
    }

def __HoldBuyJson2Obj(jsonData):
    """
    Json字符串解析为HoldBuy类对象
    """
    orderId = jsonData['orderId']
    buyTime = datetime.strptime(jsonData['buyTime'],"%Y-%m-%d %H:%M:%S")
    buyPrice = jsonData['buyPrice']
    buyAmount = jsonData['buyAmount']
    filledAmount = jsonData['filledAmount']
    finalCost = jsonData['finalCost']
    return HoldBuy(orderId,buyTime,buyPrice,buyAmount,filledAmount,finalCost)

def __OrderOperation2Json(obj):
    """
    将订单操作转为Json字符串
    """
    return {
        "orderType":obj.orderType,
        "orderTime":obj.orderTime.strftime("%Y-%m-%d %H:%M:%S"),
        "price":obj.price,
        "amount":obj.amount,
        "operationId":obj.operationId
    }

def __OrderOperationJson2Obj(jsonData):
    """
    将Json字符串转为OrderOperation类对象
    """

    if len(jsonData) == 0:
        return {}

    if isinstance(jsonData,dict):
        for key in jsonData:
            item = jsonData[key]
            if isinstance(item,OrderOperation):
                return jsonData

    orderType = jsonData['orderType']
    orderTime = datetime.strptime(jsonData['orderTime'],"%Y-%m-%d %H:%M:%S")
    price = jsonData['price']
    amount = jsonData['amount']
    operationId = jsonData['operationId']
    return OrderOperation(orderType,orderTime,price,amount,operationId)


def __SellingHoldBuy2Json(obj):
    """
    将正在出售的持有买单转为Json字符串
    """
    return {
        "orderId":obj.orderId,
        "buyTime":obj.buyTime.strftime("%Y-%m-%d %H:%M:%S"),
        "buyPrice":obj.buyPrice,
        "buyAmount":obj.buyAmount,
        "filledAmount":obj.filledAmount,
        "finalCost":obj.finalCost
    }

def __SellingHoldBuyJson2Obj(jsonData):
    """
    Json字符串解析为正在出售的持有买单
    """
    if len(jsonData) == 0:
        return {}

    if isinstance(jsonData,dict):
        for key in jsonData:
            item = jsonData[key]
            if isinstance(item,HoldBuy):
                return jsonData

    orderId = jsonData['orderId']
    buyTime = datetime.strptime(jsonData['buyTime'],"%Y-%m-%d %H:%M:%S")
    buyPrice = jsonData['buyPrice']
    buyAmount = jsonData['buyAmount']
    filledAmount = jsonData['filledAmount']
    finalCost = jsonData['finalCost']
    return HoldBuy(orderId,buyTime,buyPrice,buyAmount,filledAmount,finalCost)


def __ExchangerOrderOperation2Json(obj):
    """
    交易所订单操作转为Json字符串
    """
    return {
        "orderId":obj.orderId,
        "orderType":obj.orderType,
        "orderTime":obj.orderTime.strftime("%Y-%m-%d %H:%M:%S"),
        "price":obj.price,
        "amount":obj.amount,
        "operationId":obj.operationId,
        "state":obj.state
    }

def __ExchangerOrderOperationJson2Obj(jsonData):
    """
    Json字符串解析为交易所订单操作
    """
    if len(jsonData) == 0:
        return {}

    if isinstance(jsonData,dict):
        for key in jsonData:
            item = jsonData[key]
            if isinstance(item,ExchangerOrderOperation):
                return jsonData

    orderId = jsonData['orderId']
    orderType = jsonData['orderType']
    orderTime = datetime.strptime(jsonData['orderTime'],"%Y-%m-%d %H:%M:%S")
    price = jsonData['price']
    amount = jsonData['amount']
    operationId = jsonData['operationId']
    state = jsonData['state']
    return ExchangerOrderOperation(orderId,orderType,orderTime,price,amount,operationId,state)


def __LoadHoldBuy():
    """
    加载持有购买
    """
    global holdBuys
    if os.path.exists(__holdBuyFile):
        try:
            jsonStr = IOUtil.ReadTextFromFile(__holdBuyFile)
            holdBuys = json.loads(jsonStr,object_hook=__HoldBuyJson2Obj)
            print("HoldBuys Loaded:")
            for item in holdBuys:
                print(item)
            print("")
        except Exception as e:
            Log.Print("Fatal Error, Load hold buy file faild!",e)
            Log.Info(__logFile,"Fatal Error , Can not load hold buy data!")
            sys.exit()

def __SaveHoldBuys():
    """
    保存持有购买
    """
    global holdBuys
    jsonStr = json.dumps(holdBuys,default=__HoldBuyObj2Json)
    IOUtil.WriteTextToFile(__holdBuyFile,jsonStr)

def __LoadLocalOperations(fileName):
    """
    加载本地的订单操作
    """
    if os.path.exists(fileName):
        try:
            jsonStr = IOUtil.ReadTextFromFile(fileName)
            localOperations = json.loads(jsonStr,object_hook=__OrderOperationJson2Obj)
            return localOperations
        except Exception as e:
            Log.Print("Fatal Error, Load local operation faild! ",e,fileName)
            Log.Info(__logFile,"Fatal Error, Can not load local operation! " + fileName)
            sys.exit()

    return {}

def __SaveLocalOperations(operations, fileName):
    """
    将本地订单操作保存到文件
    """
    jsonStr = json.dumps(operations,default=__OrderOperation2Json)
    IOUtil.WriteTextToFile(fileName,jsonStr)

def __LoadLocalBuyOperations():
    """
    加载本地购买订单操作
    """
    global __localBuyOperations
    __localBuyOperations = __LoadLocalOperations(__localBuyOrdersFile)
    Log.Print("Local Buy Operations Loaded:")
    for key in __localBuyOperations:
        print(__localBuyOperations[key])
    print("")

def __SaveLocalBuyOperations():
    """
    保存本地购买订单操作
    """
    global __localBuyOperations
    __SaveLocalOperations(__localBuyOperations,__localBuyOrdersFile)


def __LoadLocalSellOperations():
    """
    加载本地卖出订单操作
    """
    global __localSellOperations
    __localSellOperations = __LoadLocalOperations(__localSellOrdersFile)
    print("Local Sell Operations Loaded:")
    for key in __localSellOperations:
        print(__localSellOperations[key])
    print("")

def __SaveLocalSellOperations():
    """
    保存本地卖出订单操作
    """
    global __localSellOperations
    __SaveLocalOperations(__localSellOperations,__localSellOrdersFile)


def __LoadExchangerOperations(fileName):
    """
    加载交易所订单操作记录
    """
    if os.path.exists(fileName):
        try:
            jsonStr = IOUtil.ReadTextFromFile(fileName)
            exchangerOperations = json.loads(jsonStr,object_hook=__ExchangerOrderOperationJson2Obj)
            return exchangerOperations
        except Exception as e:
            Log.Print("Fatal Error, Load Exchanger operation faild! ",e,fileName)
            Log.Info(__logFile,"Fatal Error, Load Exchanger Operation faild! {} {}".format(str(e),fileName))
            sys.exit()
    return {}

def __SaveExchangerOperations(operations, fileName):
    """
    将交易所订单操作保存到文件
    """
    jsonStr = json.dump(operations,default=__ExchangerOrderOperation2Json)
    IOUtil.WriteTextToFile(fileName,jsonStr)

def __LoadExchangerBuyOperations():
    """
    加载交易所买入订单操作
    """
    global __exchangerBuyOperations
    __exchangerBuyOperations = __LoadExchangerOperations(__exchangerBuyOrdersFile)
    Log.Print("Exchanger Buy Operations Loaded")
    for key in __exchangerBuyOperations:
        print(__exchangerBuyOperations[key])
    print("")

def __SaveExchangerBuyOperations():
    """
    保存交易所买入订单操作
    """
    global __exchangerBuyOperations
    __SaveExchangerBuyOperation(__exchangerBuyOperations,__exchangerBuyOrdersFile)

def __LoadExchangerSellOperations():
    """
    加载交易所卖出订单操作
    """
    global __exchangerSellOperations
    __exchangerSellOperations = __LoadExchangerOperations(__exchangerSellOrdersFile)
    Log.Print("Exchanger Sell Operations Loaded")
    for key in __exchangerSellOperations:
        print(__exchangerSellOperations[key])
    print("")

def __SaveExchangerSellOperations():
    """
    保存交易所卖出订单操作
    """
    global __exchangerSellOperations
    __SaveExchangerOperations(__exchangerSellOrdersFile,__exchangerSellOrdersFile)


def __LoadSellingHoldBuys():
    """
    加载正在出售的持有
    """
    global __sellingHoldBuys
    if os.path.exists(__sellingHoldBuyFile):
        try:
            jsonStr = IOUtil.ReadTextFromFile(fileName)
            __sellingHoldBuys = json.loads(jsonStr,object_hook=__SellingHoldBuyJson2Obj)
        except Exception as e:
            Log.Print("Fatal Error, Load Selling Hold Buys faild! {}".format(e))
            Log.Info(__logFile,"Fatal Error, Load Selling Hold Buys faild! {}".format(e))
            sys.exit()

def __SaveSellingHoldBuys():
    """
    保存正在出售的持有
    """
    global __sellingHoldBuys
    jsonStr = json.dump(__sellingHoldBuys,default=__SellingHoldBuy2Json)
    IOUtil.WriteTextToFile(__sellingHoldBuyFile,jsonStr)

def __SendLocalBuy(buyPrice,buyAmount,operationId):
    """
    进行本地下买单
    """
    global __localBuyOperations
    currTime = TimeUtil.GetShanghaiTime()
    buyOperation = OrderOperation(1,currTime,buyPrice,buyAmount,operationId)
    if __localBuyOperations.__contains__(operationId) == False:
        __localBuyOperations[operationId] = buyOperation
        Log.Print("Send local Buy: time:{} operationId:{} buyPrice:{} buyAmount:{}".format(currTime,operationId,buyPrice,buyAmount))
        Log.Info(__logFile,"Send Local Buy: time:{} operationId:{} buyPrice:{} buyAmount:{}".format(currTime,operationId,buyPrice,buyAmount))
        __SaveLocalBuyOperations()
        return True
    else:
        Log.Print("ERROR: Send local buy operation faild, already has operation:{}".format(operationId))
        Log.Info(__logFile,"ERROR: Send local buy operation faild, already has operation:{}".format(operationId))
    return False

def __SendLocalSell(sellPrice,sellAmount,operationId):
    """
    进行本地下卖单
    """
    global __localSellOperations
    currTime = TimeUtil.GetShanghaiTime()
    sellOperation = OrderOperation(0,currTime,sellPrice,sellAmount,operationId)
    if __localSellOperations.__contains__(operationId) == False:
        __localSellOperations[operationId] = sellOperation
        Log.Print("Send Local Sell: time:{} operationId:{} sellPrice:{} sellAmount:{}".format(currTime,operationId,sellPrice,sellAmount))
        Log.Info(__logFile,"Send Local Sell: time:{} operationId:{} sellPrice:{} sellAmount:{}".format(currTime,operationId,sellPrice,sellAmount))
        __SaveLocalSellOperations()
        return True
    else:
        Log.Print("ERROR: Send local sell operation faild, already has operation:{}".format(operationId))
        Log.Info(__logFile,"ERROR: Send local sell operation faild, already has operation:{}".format(operationId))
    return False



def __ExchangerOrderSendResultHandle(jsonData):
    """
    交易所下单结果处理函数
    """
    try:
        status = jsonData['status']
        if status == 'ok':
            orderId = jsonData['data']
            Log.Print("SUCCESS! Order Send, orderId:{}".format(orderId))
            Log.Info("SUCCESS! Order Send, orderId:{}".format(orderId))
            return orderId
        else:
            Log.Print("FAILD! Order Send, status:{} rawData:{}".format(status,jsonData))
            Log.Info("FAILD！Order Send, status:{} rawData:{}".format(status,jsonData))
    except Exception as e:
        Log.Print("EXCEPTION: Parse order send result data faild: rawData:{}".format(jsonData))
        Log.Info("EXCEPTION: Parse order send result data faild: rawData:{}".format(jsonData))
    return None

def __SendExchangerBuy(buyPrice,buyAmount,operationId):
    """
    与交易所通信，下买单
    """
    global __exchangerBuyOperations, __localBuyOperations
    Log.Print("Sending Exchanger Buy: operationId:{} buyPrice:{} buyAmount:{}".format(operationId,buyPrice,buyAmount))
    Log.Info("Sending Exchanger Buy: operationId:{} buyPrice:{} buyAmount:{}".format(operationId,buyPrice,buyAmount))

    # 尝试2次
    for x in range(2):
        orderData = None
        try:
            orderData = HuobiServices.send_order(buyAmount,'api',SYMBOL,'buy-limit',buyPrice)
        except Exception as e:
            orderData = None
            Log.Print("EXCEPTION: operationId:{} send buy faild! {}".format(operationId,str(e)))
            Log.Info(__logFile,"EXCEPTION: operationId:{} send buy faild! {}".format(operationId,str(e)))

        if orderData != None:
            orderId = __ExchangerOrderSendResultHandle(orderData)
            if orderId != None:
                # 下单成功
                break

    if orderId != None:
        # 下买单成功，保存交易所下单数据
        currTime = TimeUtil.GetShanghaiTime()
        exchangerBuyOperation = ExchangerOrderOperation(orderId,1,currTime,buyPrice,buyAmount,operationId)
        if __exchangerBuyOperations.__contains__(operationId) == False:
            __exchangerBuyOperations[operationId] = exchangerBuyOperation
            __SaveExchangerBuyOperations()
        else:
            Log.Print("ERROR: Send Exchanger buy operation faild, already has operation:{}".format(operationId))
            Log.Info(__logFile,"ERROR: Send Exchanger buy operation faild, already has operation:{}".format(operationId))
    else:
        Log.Print("Action: Send Exchanger Buy Order Faild , Fallback Quote Balance! operationId:{}".operationId)
        Log.Info("Action: Send Exchanger Buy Order Faild , Fallback Quote Balance! operationId:{}".operationId)
        # 下单失败，回滚本地下单数据
        localBuyOperation = __localBuyOperations.get(operationId)
        if localBuyOperation != None:
            fallbackBalance = localBuyOperation.amount * localBuyOperation.price
            BalanceManager.BuyOperationFallback(fallbackBalance)
            del __localBuyOperations[operationId]
            __SaveLocalBuyOperations()
            Log.Print("SUCCESS! Fallback Quote Balance! operationId:{}".format(operationId))
            Log.Info("SUCCESS! Fallback Quote Balance! operationId:{}".format(operationId))
        else:
            Log.Print("ERROR! Can not fallback local buy operation! operation:{}".format(operationId))
            Log.Info("ERROR! Can not fallback local buy operation! operation:{}".format(operationId))



def __SendExchangerSell(sellPrice,sellAmount,operationId):
    """
    与交易所通信，下卖单
    """
    global __exchangerSellOperations, __sellingHoldBuys
    #Log.Print("Send Exchanger Sell: operationId:{} sellPrice:{} sellAmount:{}".format(operationId,sellPrice,sellAmount))
    Log.Print("Sending Exchanger Sell: operationId:{} sellPrice:{} sellAmount:{}".format(operationId,sellPrice,sellAmount))
    Log.Info("Sending Exchanger Sell: operationId:{} sellPrice:{} sellAmount:{}".format(operationId,sellPrice,sellAmount))

    for x in range(2):
        orderData = None
        try:
            orderData = HuobiServices.send_order(sellAmount,'api',SYMBOL,'sell-limit',sellPrice)
        except Exception as e:
            orderData = None
            Log.Print("EXCEPTION: operationId:{} send Sell faild! {}".format(operationId,str(e)))
            Log.Info(__logFile,"EXCEPTION: operationId:{} send Sell faild! {}".format(operationId,str(e)))

            if orderData != None:
                orderId = __ExchangerOrderSendResultHandle(orderData)
                if orderId != None:
                    # 下单成功
                    break

    if orderId != None:
        # 下卖单成功，保存交易所下单数据
        currTime = TimeUtil.GetShanghaiTime()
        exchangerSellOperation = ExchangerOrderOperation(orderId,0,currTime,sellPrice,sellAmount,operationId)
        if __exchangerSellOperations.__contains__(operationId) == False:
            __exchangerSellOperations[operationId] = exchangerBuyOperation
            __SaveExchangerSellOperations()
        else:
            Log.Print("ERROR: Send Exchanger sell operation faild! already has operation:{}".format(operationId))
            Log.Info(__logFile,"ERROR: Send Exchanger sell operation faild! already has operation:{}".format(operationId))
    else:
        Log.Print("Action: Send Exchanger Sell Order Faild, Fallback balance, operation:{}".format(operationId))
        Log.Info(__logFile,"Action: Send Exchanger Sell Order Faild, Fallback balance, operation:{}".format(operationId))
        # 因为卖的是持有购买，只有成效了，才会造成base数据的改变，所以这里不需要回滚Balance

        # 但是要删除本地的卖单，然后将正在出售的持有放回原本持有
        del __localSellOperations[operationId]
        holdBuy = __sellingHoldBuys.get(operationId,None)
        if holdBuy != None:
            del __sellingHoldBuys[operationId]
            holdBuys.append(holdBuy)
        else:
            Log.Print("ERROR! Fallback faild! Can not found selling hold, operation:{}".format(operationId))
            Log.Info(__logFile,"ERROR! Fallback faild! Can not found selling hold, operation:{}".format(operationId))
        
        __SaveLocalSellOperations()
        __SaveSellingHoldBuys()


def __CheckBuyOrdersState():
    """
    检查所有的买单状态，是否已经成交
    """
    global __exchangerBuyOperations, holdBuys, __localBuyOperations
    for key in __exchangerBuyOperations:
        operation = __exchangerBuyOperations[key]
        if operation.state == 'end':
            continue

        orderId = operation.orderId
        try:
            sonData = HuobiServices.order_info(orderId)
            status = jsonData['status']
            if status == 'ok':
                state = jsonData['data']['state']
                if state == 'filled': # 完全成交
                    # 买单成交，删除本地买单，删除交易所买单，增加持有买单，修改资产总量，保存数据
                    operation.state = 'end'
                    amount = operation.amount * 0.997
                    amount = float("{:.4f}".format(amount))
                        
                    # 为了省事，这里多加0.3 usdt
                    cost = int(operation.amount * operation.price) + 0.3
                        
                    holdBuy = HoldBuy(orderId,operation.orderTime,operation.price,amount,amount,cost)
                    holdBuys.append(holdBuy)
                    __SaveHoldBuys()
                    __SaveExchangerBuyOperations()

                    BalanceManager.BuyFilled(amount)

                    Log.Print("FILLED! Buy Order Filled: orderId:{} amount:{} cost:{} operationId:{}".format(orderId,amount,cost,operation.operationId))
                    Log.Info(__logFile,"FILLED! Buy Order Filled: orderId:{} amount:{} cost:{} operationId:{}".format(orderId,amount,cost,operation.operationId))
                elif state == 'submitted': # 挂单中
                    pass
                elif state == 'canceled': # 订单被取消
                    pass
            else:
                Log.Print("FAILD RESULT - Check Order Info: status:{} rawJson:{}".format(status,jsonData))
        except Exception e:
            Log.Print("Exception: Check buy order state faild: orderId:{}".format(orderId))

        time.sleep(0.3) # 每检查一个单，停顿0.3秒

        # 找到所有已经end的买单，从数据中踢除
    endedOperations = []
    for key in __exchangerBuyOperations:
        operation = __exchangerBuyOperations[key]
        if operation.state == 'end':
            endedOperations.append(operation.operationId)

    for opId in endedOperations:
        del __exchangerBuyOperations[opId]
        del __localBuyOperations[opId]
        
    __SaveExchangerBuyOperations()
    __SaveLocalBuyOperations()


def __CheckSellOrdersState():
    """
    检查所有的卖单是否被成交
    """
    # 如果卖单被成交了，踢除本地卖单，踢除交易所卖单，踢除对应的持有，修改资金，保存数据
    global __exchangerSellOperations, holdBuys, __localSellOperations, sellingHoldBuy
    for key in __exchangerSellOperations:
        operation = __exchangerSellOperations[key]
        if operation.state == 'end':
            continue
        orderId = operation.orderId
        operationId = operation.operationId
        try:
            jsonData = HuobiServices.order_info(orderId)
            status = jsonData['status']
            if status == 'ok':
                state = jsonData['data']['state']
                if state == 'filled':
                    operation.state = 'end'
                    filledCash = float(jsonData['data']['field-cash-amount']) * 0.997
                    holdBuy = __sellingHoldBuys.get(operationId,None)
                    profit = filledCash - holdBuy.finalCost
                    BalanceManager.SellFilled(filledCash,profit)
                    __SaveExchangerSellOperations()

                    Log.Print("FILLED! Sell Order Filled: orderId:{} profit:{} operationId:{}".format(orderId,profit,operationId))
                    Log.Info(__logFile,"FILLED! Sell Order Filled: orderId:{} profit:{} operationId:{}".format(orderId,profit,operationId))
            else:
                Log.Print("FAILD RESULT - Check Order Info: status:{} rawJson:{}".format(status,jsonData))
        except Exception e:
            Log.Print("Exception: Check sell order state filled: orderId:{}".format(orderId))

        time.sleep(0.3)

    endedOperations = []
    for key in __exchangerSellOperations:
        operation = __exchangerSellOperations[key]
        if operation.state == 'end':
            endedOperations.append(operation.operationId)

    for opId in endedOperations:
        del __exchangerSellOperations[opId]
        del __localSellOperations[opId]
        del __sellingHoldBuys[opId]

    __SaveExchangerSellOperations()
    __SaveLocalSellOperations()
    __SaveSellingHoldBuys()


def __OrderStateCheckThread():
    global __exchangerBuyOperations, __exchangerSellOperations, holdBuys, __localBuyOperations, __localSellOperations, sellingHoldBuy
    while(True):
        __CheckBuyOrdersState()
        __CheckSellOrdersState()


def __ProofreadData():
    """
    检查以前下的订单是否已经成交，如果已经成交，则归档
    """
    Log.Print("Start Proofread Data...")
    __CheckBuyOrdersState()
    __CheckSellOrdersState()
    Log.Print("Proofread Data Finished!")


def __StartOrderCheck():
    t = threading.Thread(target=__OrderStateCheckThread)
    t.setDaemon(True)
    t.start()


def SendBuy(buyPrice,buyAmount,operationId):
    # TODO: call exchanger API to send buy order
    if __SendLocalBuy(buyPrice,buyAmount,operationId) == True:
        __SendExchangerBuy(buyPrice,buyAmount,operationId)
        

def SendSell(sellPrice,sellAmount,operationId):
    if __SendLocalSell(sellPrice,sellAmount,operationId) == True:
        __SendExchangerSell(sellPrice,sellAmount,operationId)
    


def Start():
    __LoadHoldBuy()
    __LoadLocalBuyOperations()
    __LoadLocalSellOperations()
    __LoadExchangerBuyOperations()
    __LoadExchangerSellOperations()
    __LoadSellingHoldBuys()
    __ProofreadData()
    __StartOrderCheck()



