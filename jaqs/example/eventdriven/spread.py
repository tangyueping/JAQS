import numpy as np

from jaqs.trade import common
from jaqs.trade.strategy import EventDrivenStrategy
from jaqs.data.basic.order import Order


class SpreadStrategy(EventDrivenStrategy):
    """"""
    def __init__(self):
        EventDrivenStrategy.__init__(self)
        self.symbol = ''
        
        self.s1 = ''
        self.s2 = ''
        self.quote1 = None
        self.quote2 = None

        self.window = 13
        self.pos = -1
        self.spread_arr = np.empty(self.window, dtype=float)
        
        self.threshold = 8
        
    def init_from_config(self, props):
        super(SpreadStrategy, self).init_from_config(props)
        self.symbol = props.get('symbol')
        self.init_balance = props.get('init_balance')
        
        self.s1, self.s2 = self.symbol.split(',')
    
    def on_cycle(self):
        pass
    
    def createOrder(self, quote, price, size):
        order = Order.new_order(quote.symbol, "", price, size, quote.trade_date, quote.time)
        order.order_type = common.ORDER_TYPE.LIMIT
        return order
    
    def buy(self, quote, price, size):
        order = self.createOrder(quote, price, size)
        order.entrust_action = common.ORDER_ACTION.BUY
        self.ctx.gateway.send_order(order, '', '')
    
    def sell(self, quote, price, size):
        order = self.createOrder(quote, price, size)
        order.entrust_action = common.ORDER_ACTION.SELL
        self.ctx.gateway.send_order(order, '', '')
    
    def cover(self, quote, price, size):
        order = self.createOrder(quote, price, size)
        order.entrust_action = common.ORDER_ACTION.BUY
        self.ctx.gateway.send_order(order, '', '')
    
    def short(self, quote, price, size):
        order = self.createOrder(quote, price, size)
        order.entrust_action = common.ORDER_ACTION.SELL
        self.ctx.gateway.send_order(order, '', '')
    
    def long_spread(self, quote1, quote2):
        self.buy(quote1, quote1.close, 1)
        self.sell(quote2, quote2.close, 1)

    def short_spread(self, quote1, quote2):
        self.buy(quote2, quote2.close, 1)
        self.sell(quote1, quote1.close, 1)

    def on_quote(self, quote_dic):
        q1 = quote_dic.get(self.s1)
        q2 = quote_dic.get(self.s2)
        self.quote1 = q1
        self.quote2 = q2
        
        spread = q1.close - q2.close
        self.pos += 1
        self.spread_arr[self.pos % self.window] = spread
        
        if self.pos <= self.window:
            return
        
        mean = self.spread_arr.mean()
        if (spread - mean) > self.threshold:
            self.short_spread(q1, q2)
        elif (spread - mean) < -self.threshold:
            self.long_spread(q1, q2)
    
    def on_trade_ind(self, ind):
        print(ind)
        print(self.pm.get_position(self.s1))