# encoding: UTF-8

from __future__ import absolute_import
from time import sleep
import sys
from datetime import datetime
from os.path import getmtime
import random
import requests
import math

sys.path.append("/home/yf/Downloads/vnpy-1.8/examples/VnTrader/calendar spread")

import threading
from settings import *
from utils import log, constants, errors, math
from vnpy.trader.vtObject import (VtLogData, VtSubscribeReq,
                                  VtOrderReq, VtCancelOrderReq)
from vnpy.trader.vtConstant import (PRODUCT_OPTION, OPTION_CALL, OPTION_PUT,
                                    DIRECTION_LONG, DIRECTION_SHORT,
                                    OFFSET_OPEN, OFFSET_CLOSE,
                                    PRICETYPE_LIMITPRICE,STATUS_ALLTRADED)
from vnpy.trader.vtEvent import *


GATEWAY_NAME = "OKEX"

INTERVAL = 0.001
TRANCHE_SIZE = 0.15
GRID_LEVELS = 4
GRID_TYPE = "SYMMETRIC"
grid = ["-"] * GRID_LEVELS
logger = log.setup_custom_logger('root')

class OrderManager:
    def __init__(self, mainengine,eventengine):
        try:
            logger.propagate = 0
            if settings.DRY_RUN:
                logger.info("Initializing dry run. Orders printed below represent what would be posted to BitMEX.")
            else:
                logger.info("Order Manager initializing, connecting to Okex. Live run: executing real trades.")
            self.me = mainengine
            self.ee = eventengine
            self.gateway = self.me.getGateway(GATEWAY_NAME)
            self.registerEvent()
            self.tranche_size = TRANCHE_SIZE
            self.old_quater_buy = 0
            self.old_this_week_buy = 0

        except Exception,e:
            print e

    def run_loop(self):
        try:
            while True:
                result = self.gateway.api.future_position('eos_usd','this_week')

                print result

                result = self.gateway.api.future_position('eos_usd','quarter')
                print result
                sleep(5)
            #self.gateway.api.future_trade('eos_usd', 'this_week', price='50', amount='23', tradeType='3', matchPrice='1',leverRate='10')
        except Exception,e:
            print e

    def print_status(self):
        pass

    def registerEvent(self):
        self.ee.register(EVENT_ACCOUNT, self.procecssUserInfo)
        self.ee.register(EVENT_ORDER, self.procecssOrderInfo)
        self.ee.register(EVENT_POSITION, self.procecssPositionInfo)
        self.ee.register(EVENT_TICK, self.procecssTickEvent)

    def procecssUserInfo(self,data):
        try:
            account = data.dict_['data']

            logger.info("***************UserInfo*****************")
            #logger.info("accountID %d" % account.accountID)
            logger.info("balance %f" % account.balance)
            logger.info("available %f" % account.available)

            logger.info("symbol %s" % account.symbol)
            logger.info("keep_deposit %f" % account.keep_deposit)
            logger.info("profit_real %f" % account.profit_real)
            logger.info("unit_amount %f" % account.unit_amount)
            logger.info("bond %f" % account.bond)
            logger.info("contract_id %d" % account.contract_id)
            logger.info("freeze %f" % account.freeze)
            logger.info("long_order_amount %f" % account.long_order_amount)
            logger.info("pre_long_order_amount %f" % account.pre_long_order_amount)
            logger.info("profit %f" % account.profit)
            logger.info("short_order_amount %f" % account.short_order_amount)
            logger.info("pre_short_order_amount %f" % account.pre_short_order_amount)

        except Exception,e:
            print e

    def procecssOrderInfo(self,data):
        try:
            order = data.dict_['data']
            logger.info("***************Order*****************")
            #logger.info("symbol %s" % order.symbol)
            logger.info("orderID %s" % order.orderID)
            logger.info("amount %f" % order.amount)
            logger.info("contract_name %s" % order.contract_name)
            logger.info("create_date %f" % order.create_date)
            logger.info("create_date_str %s" % order.create_date_str)
            logger.info("deal_amount %f" % order.deal_amount)
            logger.info("price %f" % order.price)
            logger.info("price_avg %f" % order.price_avg)
            logger.info("type %d" % order.type)
            logger.info("fee %f" % order.fee)
            logger.info("status %s" % order.status)
            logger.info("unit_amount %f" % order.unit_amount)
            logger.info("lever_rate %f" % order.lever_rate)
            #logger.info("value %d" % order.value)
            logger.info("system_type %d" % order.system_type)

        except Exception,e:
            print e

    def procecssPositionInfo(self,data):
        try:
            pos = data.dict_['data']
            logger.info("***************Position*****************")
            logger.info("symbol %s" % pos.symbol)
            logger.info("position %f" % pos.position)
            logger.info("contract_name %s" % pos.contract_name)
            logger.info("costprice %s" % pos.costprice)
            logger.info("bondfreez %s" % pos.bondfreez)
            logger.info("avgprice %s" % pos.avgprice)
            logger.info("contract_id %f" % pos.contract_id)
            logger.info("position_id %f" % pos.position_id)
            logger.info("hold_amount %s" % pos.hold_amount)
            logger.info("eveningup %s" % pos.eveningup)

            logger.info("margin %f" % pos.margin)
            logger.info("realized %f" % pos.realized)

        except Exception,e:
            print e
    #----------------------------------------------------------------------
    def procecssTickEvent(self, event):
        try:
            tick = event.dict_['data']

            if not tick.datetime:
                tick.datetime = datetime.strptime(' '.join([tick.date, tick.time]), '%Y%m%d %H:%M:%S.%f')
            if tick.type == 1:
                self.this_week_tick = tick
            elif tick.type == 2:
                self.next_week_tick = tick
            elif tick.type == 3:
                self.quarter_tick = tick

            self.quartervsthisweek = tick.quartervsthisweek

        except Exception,e:
            print e

    def grid_init(self):
        try:

            self.base = 0.002

            self.last_level = int(GRID_LEVELS / 2)

            logger.info("base : %f, last_level :%d" %(self.base,self.last_level))

            self.grid_debug()
        except Exception,e:
            print e

    def grid_price(self,level):
        return self.base + 0.002*level

        #return self.base * (1 + INTERVAL) ** (level - GRID_LEVELS / 2)

    def grid_place_order(self,order_type, level):
        try:
            self.matchPrice = "1"
            if 0 <= level <= GRID_LEVELS:
                #计算订单
                position_this_week = self.gateway.api.future_position('eos_usd', 'this_week')
                position_quarter = self.gateway.api.future_position('eos_usd', 'quarter')
                if order_type == 'sell':
                    #this week - buy
                    available = position_this_week['holding'][0]['sell_available']
                    amount_close = (available > self.tranche_size ? 0 : (self.tranche_size - available))
                    #order[
                    order[0]['contract_type'] = 'this_week'
                    order[0]['type'] = '1'
                    order[0]['amount'] = self.tranche_size - amount_close
                    order[1]['contract_type'] = 'this_week'
                    order[1]['type'] = '4'
                    order[1]['amount'] = str(amount_close)
                    #quarter - sell
                    available = position_quarter['holding'][0]['buy_available']
                    amount_close = (available > self.tranche_size ? 0 : self.tranche_size - available)
                    order[2]['contract_type'] = 'quarter'
                    order[2]['type'] = '2'
                    order[2]['amount'] = self.tranche_size - amount_close
                    order[3]['contract_type'] = 'quarter'
                    order[3]['type_close'] = '3'
                    order[3]['amount_close'] = str(amount_close)

                else:
                    #this week - sell
                    available = position_this_week['holding'][0]['buy_available']
                    amount_close = (available > self.tranche_size ? 0 : self.tranche_size - available)
                    order[0]['contract_type'] = 'this_week'
                    order[0]['type'] = '2'
                    order[0]['amount'] = self.tranche_size - amount_close
                    order[1]['contract_type'] = 'this_week'
                    order[1]['type'] = '3'
                    order[1]['amount] = str(amount_close)
                    #quarter - buy
                    available = position_quarter['holding'][0]['sell_available']
                    amount_close = (available > self.tranche_size ? 0 : self.tranche_size - available)
                    order[2]['contract_type'] = 'quarter'
                    order[2]['type'] = '1'
                    order[2]['amount'] = self.tranche_size - amount_close
                    order[3]['contract_type'] = 'quarter'

                    order[3]['type'] = '4'
                    order[3]['amount'] = str(amount_close)

                #下单
                for o in order:
                    o['id'], o['result'] =self.gateway.api.future_trade \
                    ('eos_usd', o['contract_type'], '', o['amount'], o['type'], self.matchPrice)


                #检查报价以及成交状态
                while True：
                    order[0]['status'] = self.future_orderinfo('eos_usd', order[0]['contract_type'], order[0]['id'], 1, 1, 1)
                    if order[0]['status']['orders'][0]['status'] != 2:
                        

                logger.info("orderid %d, result %d" % (orderid, result))
                logger.info("orderid1 %d, result1 %d" % (orderid1, result1))

            else:
                logger.info("placing order on wrong level!")
                self.grid_debug()


        except Exception, e:
            print e

        sleep(2)
        logger.info("grid_place_order level %d, grid[level] %s id %s id1 %s" % (level, orderid, orderid1))

    def future_orderinfo(self, symbol, contractType, orderId, status, currentPage, pageLength):


    def grid_debug(self):
        i = GRID_LEVELS - 1
        '''
        while i >= 0:
            if grid[i] == "" or grid [i] == "-":
                logger.info("grid %d, index %s"  % (i, grid[i]))
            else:
                for key,order in self.exchange.mainengine.dataEngine.orderDict.items():

                    if grid[i] == order.vtOrderID:
                        logger.info("grid %d, index %s price %f direction %s status %s"  % (i, grid[i], order.price, order.direction, order.status))
            i = i - 1
        '''


    def grid_main(self):
        try:
            while True:
                assert (self.quarter_tick.buy > self.this_week_tick.buy), "Quarter < This week price! stop!"

                if self.quarter_tick.buy != self.old_quater_buy or self.this_week_tick.buy != self.old_this_week_buy:
                    self.old_quarter_buy = self.quarter_tick.buy
                    self.old_this_week_buy = self.this_week_tick.buy

                    current_price = (self.quarter_tick.buy - self.this_week_tick.buy)/self.this_week_tick.buy
                    #new_level = int(math.log((1 + current_price - self.base), (1+INTERVAL)))+GRID_LEVELS/2
                    new_level = int(current_price/0.002) -1
                    if 0<=new_level<= GRID_LEVELS:
                        if new_level > self.last_level:
                            grid_place_order('sell',new_level)
                        if new_level < self.last_level-1:
                            grid_place_order('buy',new_level)
                        self.last_level = new_level
                sleep(3)

        except Exception as e:

            print e
