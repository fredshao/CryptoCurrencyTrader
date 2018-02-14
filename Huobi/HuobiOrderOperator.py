# -*- coding: utf-8 -*-
from Base.BaseOrderOperator import BaseOrderOperator

class HuobiOrderOperator(BaseOrderOperator):
    """
    火币的订单操作器
    """
    def __init__(self,symbol):
        super().__init__(symbol)
        
    def SendBuyOrder(self, buyPrice, amount):
        """
        下买单
        """
        print("Send Buy Order:",buyPrice, amount)
    
    def SendSellOrder(self, sellPrice):
        """
        下卖单
        """
        print("Send Sell Order:", sellPrice)
    
    def GetAllUnFilledOrders(self):
        """
        获取所有未成交的订单
        """
        print("Get All UnFilled Orders")
    
    def CheckOrderStatus(self, orderId):
        """
        检查订单状态
        """
        print("Check Order Status:",orderId)
    
    def CancelOrder(self, orderId):
        """
        撤销一个订单
        """
        print("Cancel Order:", orderId)