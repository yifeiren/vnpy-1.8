import time
from time import strftime

#import grequests
import os 
import sys
#from exchanges.loader import EngineLoader
from vnpy.trader.vtObject import VtOrderReq
from vnpy.trader.vtConstant import DIRECTION_LONG, DIRECTION_SHORT, OFFSET_OPEN, OFFSET_CLOSE, PRICETYPE_LIMITPRICE


GATEWAY_NAME = "OKEX"


total_earning =0
order_time =0

class CryptoEngineTriArbitrage(object):
    def __init__(self, mainengine,exchange,  connected_sig,mock=False,):
        #Yifei
        self.exchange = exchange

        #self.exchange = {
        #    'tickerPairA': 'BTC-ETH',
        #    'tickerPairB': 'ETH-LTC',
        #    'tickerPairC': 'BTC-LTC',
        #    'tickerA': 'BTC',
        #    'tickerB': 'ETH',
        #    'tickerC': 'LTC'
        #}
        #self.exchange = {
        #    'tickerPairA': 'gnx_eth',
        #    'tickerPairB': 'eth_btc',
        #    'tickerPairC': 'gnx_btc',
        #    'tickerA': 'gnx',
        #    'tickerB': 'eth',
        #    'tickerC': 'btc'
        #}
        self.mainengine = mainengine

        self.mock = mock
        self.minProfitUSDT = 0.3
        self.hasOpenOrder = True # always assume there are open orders first
        self.openOrderCheckCount = 0
        #Yifei
        self.sleepTime = 0.001
        self.openOrders = []
        self.balance = 0
        self.feeRatio = 0.0015
        self.event1 = connected_sig

        #self.engine = EngineLoader.getEngine(self.exchange['exchange'], self.exchange['keyFile'])

    def start_engine(self):
        print strftime('%Y%m%d%H%M%S') + ' starting Triangular Arbitrage Engine...'
        if self.mock:
            print '---------------------------- MOCK MODE ----------------------------'
        #Send the request asynchronously
        gw = self.mainengine.getGateway(GATEWAY_NAME)
        self.event1.wait()
        time.sleep(8)
        while True:
            try:

                #if gw.connected == True and gw.api_spot.tickDict.__len__ != 0:

                #if not self.mock and self.hasOpenOrder:
                #if not self.mock:

                #    self.check_openOrder()
                #elif self.check_balance():
                if self.check_balance():
                    bookStatus = self.check_orderBook()
                    if bookStatus['status']:
                        self.place_order(bookStatus['orderInfo'])
                        if not self.mock:
                            time.sleep(8)
                time.sleep(self.sleepTime)

            except Exception, e:
               # raise
               print e
            

    def check_openOrder(self):
        try:
            if self.openOrderCheckCount >= 5:
                #self.cancel_allOrders()
                1
            else:
                print 'checking open orders...'
                #Yifei
                #rs = [self.engine.get_open_order()]
                #responses = self.send_request(rs)
                self.openOrders = self.mainengine.getAllOrders()
                #gw = self.mainengine.getGateway(GATEWAY_NAME)
                #gw.qryOrderInfo()
                #if not responses:
                #    print responses
                #    return False

                if self.openOrders:
                    #Yifei
                    #self.engine.openOrders = responses[0].parsed
                    #self.openOrders = gw.api_spot.orderDict

                    #Yifei
                    #print self.engine.openOrders
                    print self.openOrders
                    self.openOrderCheckCount += 1
                else:
                    self.hasOpenOrder = False
                    print 'no open orders'
                    print 'starting to check order book...'

        except Exception, e:
        # raise
            print e

    def cancel_allOrders(self):
        try:
            print 'cancelling all open orders...'
            #rs = []
            #Yifei
            #print self.exchange['exchange']
            #for order in self.engine.openOrders:
            for i,order in enumerate(self.openOrders):
                print order
                #Yifei
                #rs.append(self.engine.cancel_order(order['orderId']))
                self.mainengine.cancelOrder(order,GATEWAY_NAME)
            #responses = self.send_request(rs)

            #self.engine.openOrders = []
            self.openOrders = []
            self.hasOpenOrder = False
        except Exception, e:
            # raise
            print e

    #Check and set current balance
    def check_balance(self):
        try:
            #Yifei
            rs = []
            #rs = [self.engine.get_balance([
            #    self.exchange['tickerA'],
            #    self.exchange['tickerB'],
            #    self.exchange['tickerC']
            #    ])]

            #responses = self.send_request(rs)

            #rs.append(self.mainengine.getPositionDetail("usdt"))
            #rs.append(self.mainengine.getPositionDetail(self.exchange['tickerB']))
            #rs.append(self.mainengine.getPositionDetail(self.exchange['tickerC']))
            rs = self.mainengine.getAllPositions()
            dict = {}
            for position in rs:
                dict[position.vtPositionName]=(position.position)
                if self.mock == True:
                    dict[position.vtPositionName] = 100000000000
            #self.engine.balance = responses[0].parsed
            self.balance = dict
        except Exception, e:
            # raise
            print e

        ''' Not needed? '''
        # if not self.mock:
        #     for res in responses:
        #         for ticker in res.parsed:
        #             if res.parsed[ticker] < 0.05:
        #                 print ticker, res.parsed[ticker], '- Not Enough'
        #                 return False
        return True
    
    def check_orderBook(self):


        global total_earning
        global order_time
        try:
            lastPrices = []
            gw=self.mainengine.getGateway(GATEWAY_NAME)
            lastPrices.append(gw.api_spot.tickDict[self.exchange['tickerA']+'_usdt'].lastPrice)
            lastPrices.append(gw.api_spot.tickDict[self.exchange['tickerB']+'_usdt'].lastPrice)
            lastPrices.append(gw.api_spot.tickDict[self.exchange['tickerC']+'_usdt'].lastPrice)


            bidRoute_result = (1 / float(gw.api_spot.tickDict[self.exchange['tickerPairA']].askPrice1)) \
                              / float(gw.api_spot.tickDict[self.exchange['tickerPairB']].askPrice1) \
                              * float(gw.api_spot.tickDict[self.exchange['tickerPairC']].bidPrice1)


            askRoute_result = (1 * float(gw.api_spot.tickDict[self.exchange['tickerPairA']].bidPrice1)) \
                              / float(gw.api_spot.tickDict[self.exchange['tickerPairC']].askPrice1) \
                              * float(gw.api_spot.tickDict[self.exchange['tickerPairB']].bidPrice1)

            # Max amount for bid route & ask routes can be different and so less profit
            if bidRoute_result > 1 or \
            (bidRoute_result > 1 and askRoute_result > 1 and (bidRoute_result - 1) * lastPrices[0] > (askRoute_result - 1) * lastPrices[1]):
                status = 1 # bid route
            elif askRoute_result > 1:
                status = 2 # ask route
            else:
                status = 0 # do nothing
            #status =1
            #print 'bidRoute_result {0}\naskRoute_result {1} '.format(bidRoute_result, askRoute_result)

            if status > 0:
                if bidRoute_result>=1+self.feeRatio or askRoute_result>=1+self.feeRatio:
                #if order_time == 0:
                    if 0:
                        print '************************************************************************'
                        print '{0}'.format(self.exchange['tickerPairA'])
                        print 'ask price {0}, \nask volume {1},\nbid price {2},\nbid volume {3}'.format(
                            gw.api_spot.tickDict[self.exchange['tickerPairA']].askPrice1,
                            gw.api_spot.tickDict[self.exchange['tickerPairA']].askVolume1,
                            gw.api_spot.tickDict[self.exchange['tickerPairA']].bidPrice1,
                            gw.api_spot.tickDict[self.exchange['tickerPairA']].bidVolume1)

                        print '{0}'.format(self.exchange['tickerPairB'])
                        print 'ask price {0}, \nask volume {1},\nbid price {2},\nbid volume {3}'.format(
                            gw.api_spot.tickDict[self.exchange['tickerPairB']].askPrice1,
                            gw.api_spot.tickDict[self.exchange['tickerPairB']].askVolume1,
                            gw.api_spot.tickDict[self.exchange['tickerPairB']].bidPrice1,
                            gw.api_spot.tickDict[self.exchange['tickerPairB']].bidVolume1)

                        print '{0}'.format(self.exchange['tickerPairC'])
                        print 'ask price {0}, \nask volume {1},\nbid price {2},\nbid volume {3}'.format(
                            gw.api_spot.tickDict[self.exchange['tickerPairC']].askPrice1,
                            gw.api_spot.tickDict[self.exchange['tickerPairC']].askVolume1,
                            gw.api_spot.tickDict[self.exchange['tickerPairC']].bidPrice1,
                            gw.api_spot.tickDict[self.exchange['tickerPairC']].bidVolume1)

                        print 'bidRoute_result {0}\naskRoute_result {1} '.format(bidRoute_result, askRoute_result)

                        print 'Status {0}\n'.format(status)

                    if status == 1:
                        maxAmounts = self.getMaxAmount(lastPrices, gw.api_spot.tickDict, status,bidRoute_result )
                    else:
                        maxAmounts = self.getMaxAmount(lastPrices, gw.api_spot.tickDict, status, bidRoute_result)

                    fee = 0
                    for index, amount in enumerate(maxAmounts):
                        fee += amount * lastPrices[index]

                    fee *= self.feeRatio

                    bidRoute_profit = (bidRoute_result - 1) * lastPrices[0] * maxAmounts[0]
                    askRoute_profit = (askRoute_result - 1) * lastPrices[1] * maxAmounts[1]
                    #print 'bidRoute_profit - {0} askRoute_profit - {1} fee - {2}'.format(
                    #    bidRoute_profit, askRoute_profit, fee
                    #)
                    #if status == 1 and order_time ==0:
                    if bidRoute_profit - fee > self.minProfitUSDT:

                        print 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'
                        total_earning += bidRoute_profit - fee
                        #print 'bidRoute_profit - {0} askRoute_profit - {1} fee - {2} earning {3}, total_earning {4}'.format(
                        #    bidRoute_profit, askRoute_profit, fee, bidRoute_profit-fee, total_earning
                        #)

                        print strftime('%Y%m%d%H%M%S') + ' Bid Route: Result : {0} Profit : {1} Fee : {2}, total_earning: {3}'.format(bidRoute_result, bidRoute_profit, fee, total_earning)
                        print 'ticker {0}'.format(self.exchange['tickerPairA'])
                        orderInfo = [
                            {
                                "tickerPair": self.exchange['tickerPairA'],
                                "action": "bid",
                                "price": gw.api_spot.tickDict[self.exchange['tickerPairA']].askPrice1 ,
                                "amount": maxAmounts[0]
                            },
                            {
                                "tickerPair": self.exchange['tickerPairB'],
                                "action": "bid",
                                "price": gw.api_spot.tickDict[self.exchange['tickerPairB']].askPrice1 ,

                                "amount": maxAmounts[1]
                            },
                            {
                                "tickerPair": self.exchange['tickerPairC'],
                                "action": "ask",
                                "price": gw.api_spot.tickDict[self.exchange['tickerPairC']].bidPrice1 ,
                                "amount": maxAmounts[2]*lastPrices[2]/lastPrices[0]
                            }
                        ]
                        return {'status': 1, "orderInfo": orderInfo}

                    elif askRoute_profit - fee > self.minProfitUSDT:
                    #elif status == 2 and order_time == 0:

                        print 'BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB'

                        total_earning += askRoute_profit - fee
                        #print 'bidRoute_profit - {0} askRoute_profit - {1} fee - {2} earning {3}, total_earning {4}'.format(
                        #    bidRoute_profit, askRoute_profit, fee, askRoute_profit-fee, total_earning
                        #)
                        #print 'bidRoute_profit - {0} askRoute_profit - {1} fee - {2} earning {3}'.format(
                        #    bidRoute_profit, askRoute_profit, fee, askRoute_profit - fee
                        #)
                        print strftime('%Y%m%d%H%M%S') + ' Ask Route: Result : {0} Profit : {1} Fee : {2} Total_earning : {3}'.format(askRoute_result, askRoute_profit, fee, total_earning)
                        print 'ticker {0}'.format(self.exchange['tickerPairA'])
                        orderInfo = [
                            {
                                "tickerPair": self.exchange['tickerPairA'],
                                "action": "ask",
                                "price": gw.api_spot.tickDict[self.exchange['tickerPairA']].bidPrice1,

                                "amount": maxAmounts[0]
                            },
                            {
                                "tickerPair": self.exchange['tickerPairB'],
                                "action": "ask",
                                "price": gw.api_spot.tickDict[self.exchange['tickerPairB']].bidPrice1,
                                "amount": maxAmounts[1]
                            },
                            {
                                "tickerPair": self.exchange['tickerPairC'],
                                "action": "bid",
                                "price": gw.api_spot.tickDict[self.exchange['tickerPairC']].askPrice1,
                                "amount": maxAmounts[2]*lastPrices[2]/lastPrices[0]
                            }
                        ]
                        return {'status': 2, 'orderInfo': orderInfo}
            return {'status': 0}
        except Exception, e:
            # raise
            print e
            # Yifei
            # rs = [self.engine.get_ticker_lastPrice(self.exchange['tickerA']),
            #    self.engine.get_ticker_lastPrice(self.exchange['tickerB']),
            #    self.engine.get_ticker_lastPrice(self.exchange['tickerC']),
            # ]


            #Yifei
            #rs = [self.engine.get_ticker_orderBook_innermost(self.exchange['tickerPairA']),
            #      self.engine.get_ticker_orderBook_innermost(self.exchange['tickerPairB']),
            #      self.engine.get_ticker_orderBook_innermost(self.exchange['tickerPairC']),
            #      ]
            #responses =[]
            #responses[0].parsed['ask']['price'] = gw.api_spot.tickDict[self.exchange['tickerA']].askPrice1
            #responses[0].parsed['bid']['price'] = gw.api_spot.tickDict[self.exchange['tickerA']].bidPrice1
            #responses[0].parsed['ask']['amount'] = gw.api_spot.tickDict[self.exchange['tickerA']].askVolume1
            #responses[0].parsed['bid']['amount'] = gw.api_spot.tickDict[self.exchange['tickerA']].bidVolume1

            #responses[1].parsed['ask']['price'] = gw.api_spot.tickDict[self.exchange['tickerB']].askPrice1
            #responses[1].parsed['bid']['price'] = gw.api_spot.tickDict[self.exchange['tickerB']].bidPrice1
            #responses[1].parsed['ask']['amount'] = gw.api_spot.tickDict[self.exchange['tickerB']].askVolume1
            #responses[1].parsed['bid']['amount'] = gw.api_spot.tickDict[self.exchange['tickerB']].bidVolume1

            #responses[2].parsed['ask']['price'] = gw.api_spot.tickDict[self.exchange['tickerC']].askPrice1
            #responses[2].parsed['bid']['price'] = gw.api_spot.tickDict[self.exchange['tickerC']].bidPrice1
            #responses[2].parsed['ask']['amount'] = gw.api_spot.tickDict[self.exchange['tickerC']].askVolume1
            #responses[2].parsed['bid']['amount'] = gw.api_spot.tickDict[self.exchange['tickerC']].bidVolume1



            #responses = self.send_request(rs)

            #if self.mock:

                #print '{0}'.format(self.exchange['tickerPairA'])
                #print '{0} - {1}; \n{2} - {3}; \n{4} - {5}'.format(
                #    self.exchange['tickerPairA'],
                    #responses[0].parsed,
                #    None,
                    #gw.api_spot.tickDict[self.exchange['tickerPairA']].__dict__,
                #    self.exchange['tickerPairB'],
                    #responses[1].parsed,
                    #gw.api_spot.tickDict[self.exchange['tickerPairB']].__dict__,
                #    None,
                #    self.exchange['tickerPairC'],
                    #responses[2].parsed
                    #gw.api_spot.tickDict[self.exchange['tickerPairC']].__dict__
                #    None
                #    )
            # bid route BTC->ETH->LTC->BTC
            #bidRoute_result = (1 / responses[0].parsed['ask']['price']) \
            #                    / responses[1].parsed['ask']['price']   \
            #                    * responses[2].parsed['bid']['price']

            # ask route ETH->BTC->LTC->ETH
            # askRoute_result = (1 * responses[0].parsed['bid']['price']) \
            #                    / responses[2].parsed['ask']['price']   \
            #                    * responses[1].parsed['bid']['price']

            # maxAmounts = self.getMaxAmount(lastPrices, responses, status)
            # Yifei
            # fee *= self.engine.feeRatio
    # Using USDT may not be accurate
    def getMaxAmount(self, lastPrices, tickDict, status, route_result):
        try:
            maxUSDT = []

            if status == 1 :
                maxUSDT= min(float(tickDict[self.exchange['tickerPairA']].askVolume1)
                    *float(tickDict[self.exchange['tickerPairA']].askPrice1)
                             *lastPrices[1],
                    float(tickDict[self.exchange['tickerPairB']].askVolume1)
                    * float(tickDict[self.exchange['tickerPairB']].askPrice1)
                             *lastPrices[2],
                    float(tickDict[self.exchange['tickerPairC']].bidVolume1)
                    * float(tickDict[self.exchange['tickerPairC']].bidPrice1)
                             *lastPrices[2]
                    )
            else:
                maxUSDT=min(float(tickDict[self.exchange['tickerPairA']].bidVolume1)
                    *float(tickDict[self.exchange['tickerPairA']].bidPrice1)
                            *lastPrices[1],
                    float(tickDict[self.exchange['tickerPairB']].bidVolume1)
                    * float(tickDict[self.exchange['tickerPairB']].bidPrice1)
                            *lastPrices[2],
                    float(tickDict[self.exchange['tickerPairC']].askVolume1)
                    * float(tickDict[self.exchange['tickerPairC']].askPrice1)
                            *lastPrices[2]
                    )
            print 'maxUSDT in market {0}\n'.format(maxUSDT)


            tmpUSDT = min(self.balance[self.exchange['tickerA']]*lastPrices[0],
                          self.balance[self.exchange['tickerB']]*lastPrices[1],
                          self.balance[self.exchange['tickerC']] * lastPrices[2]
                          )

            maxUSDT = min(maxUSDT,tmpUSDT)

            print 'maxUSDT in portofolio {0}\n'.format(tmpUSDT)


                #print 'maxUSDT!!! {0}\n'.format(maxUSDT)

            #for index, tickerIndex in enumerate([self.exchange['tickerA'], self.exchange['tickerB'], self.exchange['tickerC']]):
                # 1: 'bid', -1: 'ask'
            #    if index == 0: bid_ask = -1
            #    elif index == 1: bid_ask = -1
            #    else: bid_ask = 1
                # switch for ask route
            #    if status == 2: bid_ask *= -1
            #    bid_ask = 'ask' if bid_ask == 1 else 'bid'
#Yifei
                #maxBalance = min(orderBookRes[index].parsed[bid_ask]['amount'], self.balance[self.exchange[tickerIndex]])
            #   if index ==0:
            #        if bid_ask =='bid':
            #            maxBalance = min(float(tickDict[self.exchange['tickerPairA']].askVolume1),
            #                             self.balance[self.exchange['tickerA']])
            #        else:
            #            maxBalance = min(float(tickDict[self.exchange['tickerPairA']].bidVolume1),
            #                     self.balance[self.exchange['tickerA']])
            #    elif index==1:
            #        if bid_ask =='bid':
            #            maxBalance = min(float(tickDict[self.exchange['tickerPairB']].askVolume1),
            #                             self.balance[self.exchange['tickerB']])
            #        else:
            #            maxBalance = min(float(tickDict[self.exchange['tickerPairB']].bidVolume1),
            #                     self.balance[self.exchange['tickerB']])
            #    elif index == 2:
            #        if bid_ask == 'bid':
            #            maxBalance = min(float(float(tickDict[self.exchange['tickerPairC']].askVolume1)*lastPrices[0]/lastPrices[2]),
            #                             self.balance[self.exchange['tickerC']])
            #        else:
            #            maxBalance = min(float(float(tickDict[self.exchange['tickerPairC']].bidVolume1)*lastPrices[0]/lastPrices[2]),
            #                             self.balance[self.exchange['tickerC']])
                # print '{0} orderBookAmount - {1} ownAmount - {2}'.format(
                #     self.exchange[tickerIndex],
                #     orderBookRes[index].parsed[bid_ask]['amount'],
                #     self.engine.balance[self.exchange[tickerIndex]]
                # )
                #USDT = maxBalance * lastPrices[index] * (1 - self.engine.feeRatio)

                #print 'maxBalance \n{0}'.format(maxBalance)

            #   USDT = maxBalance * lastPrices[index] * (1 - self.feeRatio)
            #   if not maxUSDT or USDT < maxUSDT:
            #       maxUSDT = USDT

            #    print 'maxUSDT*** {0}\n'.format(maxUSDT)

            if maxUSDT * (route_result -1 -self.feeRatio) > self.minProfitUSDT:

                print 'maxUSDT {0}\n'.format(maxUSDT)


                print '{0} - {1}; \n{2} - {3}; \n{4} - {5}'.format(
                    self.exchange['tickerPairA'],
                    tickDict[self.exchange['tickerPairA']].__dict__,
                    self.exchange['tickerPairB'],
                    tickDict[self.exchange['tickerPairB']].__dict__,
                    self.exchange['tickerPairC'],
                    tickDict[self.exchange['tickerPairC']].__dict__
                )

                print 'last price\n{0}; \n{1}; \n{2}'.format(
                    lastPrices[0],
                    lastPrices[1],
                    lastPrices[2]

                )

                print 'Balance\n{0}; \n{1}; \n{2}'.format(
                    self.balance[self.exchange['tickerA']],
                    self.balance[self.exchange['tickerB']],
                    self.balance[self.exchange['tickerC']]

                )

                print 'Status {0}'.format(
                    status
                )
            maxAmounts = []
            for index, tickerIndex in enumerate([self.exchange['tickerA'], self.exchange['tickerB'], self.exchange['tickerC']]):
                # May need to handle scientific notation
                maxAmounts.append(maxUSDT / lastPrices[index])
                #print 'maxAmount {0} maxUSDT {1} last Prices {2}\n'.format( maxUSDT/lastPrices[index],maxUSDT,lastPrices[index])

            return maxAmounts

        except Exception, e:
        # raise
            print e

    def place_order(self, orderInfo):
        global order_time

        try:
            print orderInfo
            #rs = []
            req = VtOrderReq()
            for order in orderInfo:
                req.symbol = order['tickerPair']
                if order['action']=='bid':
                    req.direction = DIRECTION_LONG
                else:
                    req.direction = DIRECTION_SHORT
                #req.direction = order['action']
                req.volume = order['amount']
                req.price = order['price']
                req.priceType= PRICETYPE_LIMITPRICE

                #if not self.mock and order_time == 0:
                if not self.mock:
                    self.mainengine.getGateway(GATEWAY_NAME).sendOrder(req)


            #if not self.mock:
            #    responses = self.send_request(rs)
            order_time = 1
            self.hasOpenOrder = True
            self.openOrderCheckCount = 0
        except Exception, e:
            # raise
            print e

            #   def send_request(self, rs):
 #       responses = grequests.map(rs)
 #       for res in responses:
 #           if not res:
 #               print responses
 #               raise Exception
 #       return responses

    def run(self):
        self.start_engine()

