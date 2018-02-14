# -*- coding: utf-8 -*-
# 所有的订单操作


class Order:
    def __init__(self, orderId):
        pass


class BaseOrderOperator:
    def __init__(self, symbol):
        self.symbol = symbol
    
    def SendBuyOrder(self,buyPrice):
        """
        下买单
        """
        pass
    
    def SendSellOrder(self, sellPrice):
        """
        下卖单
        """
        pass
    
    def GetAllUnFilledOrders(self):
        """
        获取所有未成交的订单
        """
        pass
    
    def CheckOrderStatus(self,orderId):
        """
        检查订单的状态
        """
        pass
    
    def CancelOrder(self,orderId):
        """
        取消一个订单
        """
        pass
    
        