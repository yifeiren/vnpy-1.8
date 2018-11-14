from __future__ import absolute_import
from time import sleep
import sys
from datetime import datetime
from os.path import getmtime
import random
import requests
import atexit
import signal

sys.path.append("/home/yf/Downloads/vnpy-1.8/examples/VnTrader/market maker")

#from market_maker import bitmex
import threading
from settings import *
from utils import log, constants, errors, math
#Yifei
from vnpy.trader.vtObject import (VtLogData, VtSubscribeReq,
                                  VtOrderReq, VtCancelOrderReq)
from vnpy.trader.vtConstant import (PRODUCT_OPTION, OPTION_CALL, OPTION_PUT,
                                    DIRECTION_LONG, DIRECTION_SHORT,
                                    OFFSET_OPEN, OFFSET_CLOSE,
                                    PRICETYPE_LIMITPRICE,STATUS_ALLTRADED)

# Used for reloading the bot - saves modified times of key files
import os
#watched_files_mtimes = [(f, getmtime(f)) for f in settings.WATCHED_FILES]

#Yifei
GATEWAY_NAME = "OKEX"
timer = None


INTERVAL = 0.003
TRANCHE_SIZE = 0.15
GRID_LEVELS = 20
#GRID_BASE = config.get('grid', 'base').upper()
GRID_TYPE = "SYMMETRIC"
grid = ["-"] * GRID_LEVELS
#
# Helpers
#
logger = log.setup_custom_logger('root')


class ExchangeInterface:
    def __init__(self, mainengine,dry_run=False):
        self.dry_run = dry_run
        if len(sys.argv) > 1:
            self.symbol = sys.argv[1]
        else:
            self.symbol = settings.SYMBOL

        #Yifei
        #self.bitmex = bitmex.BitMEX(base_url=settings.BASE_URL, symbol=self.symbol,
        #                            apiKey=settings.API_KEY, apiSecret=settings.API_SECRET,
        #                            orderIDPrefix=settings.ORDERID_PREFIX, postOnly=settings.POST_ONLY,
        #                            timeout=settings.TIMEOUT)

        self.mainengine = mainengine
        self.gw = self.mainengine.getGateway(GATEWAY_NAME)


    def cancel_order(self, order):


        try:
            #Yifei
            #tickLog = self.get_instrument()['tickLog']
            #logger.info("Canceling: %s %d @ %.*f" % (order['side'], order['orderQty'], tickLog, order['price']))
            logger.info("Canceling: %s %d @ %.*f" % (order.direction, order.volume, order.price))
            if not self.dry_run:
                self.mainengine.cancelOrder(order, GATEWAY_NAME)

            #while True:
            #    try:
            #        self.bitmex.cancel(order['orderID'])
            #        sleep(settings.API_REST_INTERVAL)
            #    except ValueError as e:
            #        logger.info(e)
            #        sleep(settings.API_ERROR_INTERVAL)
            #    else:
            #        break

        except Exception, e:
        # raise
            print e
    def cancel_all_orders(self):
        try:
            logger.info("Resetting current position. Canceling all existing orders.")
            #tickLog = self.get_instrument()['tickLog']

            # In certain cases, a WS update might not make it through before we call this.
            # For that reason, we grab via HTTP to ensure we grab them all.
            #orders = self.bitmex.http_open_orders()
            orders = self.get_orders()

            for order in orders:
                logger.info("Canceling: %s %d @ %.f" % (order['side'], order['orderQty'], order['price']))
                if not self.dry_run:
                    self.mainengine.cancelOrder(order, GATEWAY_NAME)

            #if len(orders):
            #    self.bitmex.cancel([order['orderID'] for order in orders])

            sleep(settings.API_REST_INTERVAL)

        except Exception, e:
            # raise
            print e


    #def get_portfolio(self):
    #    contracts = settings.CONTRACTS
    #    portfolio = {}
    #    for symbol in contracts:
    #        position = self.bitmex.position(symbol=symbol)
    #        instrument = self.bitmex.instrument(symbol=symbol)

    #        if instrument['isQuanto']:
    #            future_type = "Quanto"
    #        elif instrument['isInverse']:
    #            future_type = "Inverse"
    #        elif not instrument['isQuanto'] and not instrument['isInverse']:
    #            future_type = "Linear"
    #        else:
    #            raise NotImplementedError("Unknown future type; not quanto or inverse: %s" % instrument['symbol'])

    #        if instrument['underlyingToSettleMultiplier'] is None:
    #            multiplier = float(instrument['multiplier']) / float(instrument['quoteToSettleMultiplier'])
    #        else:
    #            multiplier = float(instrument['multiplier']) / float(instrument['underlyingToSettleMultiplier'])

    #        portfolio[symbol] = {
    #            "currentQty": float(position['currentQty']),
    #            "futureType": future_type,
    #            "multiplier": multiplier,
    #            "markPrice": float(instrument['markPrice']),
    #            "spot": float(instrument['indicativeSettlePrice'])
    #        }

    #    return portfolio

    #def calc_delta(self):
    #    """Calculate currency delta for portfolio"""
    #    portfolio = self.get_portfolio()
    #    spot_delta = 0
    #    mark_delta = 0
    #    for symbol in portfolio:
    #        item = portfolio[symbol]
    #        if item['futureType'] == "Quanto":
    #            spot_delta += item['currentQty'] * item['multiplier'] * item['spot']
    #            mark_delta += item['currentQty'] * item['multiplier'] * item['markPrice']
    #        elif item['futureType'] == "Inverse":
    #            spot_delta += (item['multiplier'] / item['spot']) * item['currentQty']
    #            mark_delta += (item['multiplier'] / item['markPrice']) * item['currentQty']
    #        elif item['futureType'] == "Linear":
    #            spot_delta += item['multiplier'] * item['currentQty']
    #            mark_delta += item['multiplier'] * item['currentQty']
    #    basis_delta = mark_delta - spot_delta
    #    delta = {
    #        "spot": spot_delta,
    #        "mark_price": mark_delta,
    #        "basis": basis_delta
    #    }
    #    return delta

    def get_delta(self, symbol=None):
        try:
            if symbol is None:
                symbol = self.symbol
            #Yifei
            rs = []
            rs = self.mainengine.getAllPositions()
            for position in rs:
                if symbol == position.vtPositionName:
                    return position.postion
            return 0
        except Exception, e:
            # raise
            print e

    #def get_instrument(self, symbol=None):
    #    if symbol is None:
    #        symbol = self.symbol
    #    return self.bitmex.instrument(symbol)

    #def get_margin(self):
    #    if self.dry_run:
    #        return {'marginBalance': float(settings.DRY_BTC), 'availableFunds': float(settings.DRY_BTC)}
    #    return self.bitmex.funds()

    def get_orders(self):
        #if self.dry_run:
        #    return []
        #return self.bitmex.open_orders()
        return self.mainengine.getAllWorkingOrders()

    def get_highest_buy(self):
        buys = [o for o in self.get_orders() if o.direction == DIRECTION_LONG]
        if not len(buys):
            return {'price': -2**32}
        highest_buy = max(buys or [], key=lambda o: o.price)
        return {'price':highest_buy.price} if highest_buy else {'price': -2**32}

    def get_lowest_sell(self):
        #sells = [o for o in self.get_orders() if o['side'] == 'Sell']
        sells = [o for o in self.get_orders() if o.direction == DIRECTION_SHORT]
        if not len(sells):
            return {'price': 2**32}
        lowest_sell = min(sells or [], key=lambda o: o.price)
        return {'price': lowest_sell.price} if lowest_sell else {'price': 2**32}  # ought to be enough for anyone

    #def get_position(self, symbol=None):
    #    if symbol is None:
    #        symbol = self.symbol
    #    return self.bitmex.position(symbol)

    def get_ticker(self, symbol=None):
        if symbol is None:
            symbol = self.symbol
        #return self.bitmex.ticker_data(symbol)
        return self.gw.api_spot.tickDict[symbol]

    def is_open(self):
        """Check that websockets are still open."""
        return self.gw.connected

    #def check_market_open(self):
    #    instrument = self.get_instrument()
    #    if instrument["state"] != "Open" and instrument["state"] != "Closed":
    #        raise errors.MarketClosedError("The instrument %s is not open. State: %s" %
    #                                       (self.symbol, instrument["state"]))

    #def check_if_orderbook_empty(self):
    #    """This function checks whether the order book is empty"""
    #    instrument = self.get_instrument()
    #    if instrument['midPrice'] is None:
    #        raise errors.MarketEmptyError("Orderbook is empty, cannot quote")

    #def amend_bulk_orders(self, orders):
    #    if self.dry_run:
    #        return orders
    #    return self.bitmex.amend_bulk_orders(orders)

    def create_bulk_orders(self, orders):
        try:

            req = VtOrderReq()
            for order in orders:
                req.symbol = self.symbol
                if order['side']=='Buy':
                    req.direction = DIRECTION_LONG
                elif order['side'] =='Sell':
                    req.direction = DIRECTION_SHORT
                else:
                    logger.error("Create_bulk_orders: Order direction is worng!")
                req.volume = order['orderQty']
                req.price = order['price']
                req.priceType= PRICETYPE_LIMITPRICE

                if not self.dry_run:
                    if  req.direction == DIRECTION_LONG and self.mainengine.dataEngine.positionDict['eth'].position -self.mainengine.dataEngine.positionDict['eth'].frozen > settings.ORDER_START_SIZE * float(self.get_ticker().bidPrice1) or req.direction == DIRECTION_SHORT and self.mainengine.dataEngine.positionDict['ada'].position -self.mainengine.dataEngine.positionDict['ada'].frozen > settings.ORDER_START_SIZE:
                        self.mainengine.getGateway(GATEWAY_NAME).sendOrder(req)
                    else:
                        logger.info("no sufficent money!")
            sleep(settings.API_REST_INTERVAL)
            self.mm_debug()

        except Exception, e:
            print e

    #return {'price': price, 'orderQty': quantity, 'side': "Buy" if index < 0 else "Sell"}
    def cancel_bulk_orders(self, orders):
        try:
            for order in orders:
                if not self.dry_run:
                    self.mainengine.cancelOrder(order, GATEWAY_NAME)
            sleep(settings.API_REST_INTERVAL)
            self.mm_debug()

        except Exception, e:
            print e

        #return self.bitmex.cancel([order['orderID'] for order in orders])
    def place_order(self,req):
        if not self.dry_run:
            id = self.mainengine.getGateway(GATEWAY_NAME).sendOrder(req)
            self.mm_debug()

        return id

    #def getOrderHistory(self):
    #    orders_all = self.mainengine.getAllOrders()
    #    orders_working = self.mainengine.getAllWorkingOrders()
    #    orders_history = orders_all

    #    for order in orders_history:
    #        if order.vtOrderID in orders_working:
    #            del orders_history[order.vtOrderID]

    #    return orders_history
    def mm_debug(self):

        for key,order in self.mainengine.dataEngine.orderDict.items():

            logger.info("price %f direction %s status %s"  % (order.price, order.direction, order.status))

class OrderManager:
    #Yifei
    #def __init__(self ):
    def __init__(self, mainengine):
        #elf.symbol = symbol

        self.exchange = ExchangeInterface(mainengine,settings.DRY_RUN)
        # Once exchange is created, register exit handler that will always cancel orders
        # on any error.
        atexit.register(self.exit)
        signal.signal(signal.SIGTERM, self.exit)

        #logger.info("Using symbol %s." % self.symbol)

        if settings.DRY_RUN:
            logger.info("Initializing dry run. Orders printed below represent what would be posted to BitMEX.")
        else:
            logger.info("Order Manager initializing, connecting to Okex. Live run: executing real trades.")

        self.start_time = datetime.now()
        #self.instrument = self.exchange.get_instrument()
        #self.starting_qty = self.exchange.get_delta()
        #self.running_qty = self.starting_qty
        #self.reset()
        #self.grid_init()

    def reset(self):
        self.exchange.cancel_all_orders()
        self.sanity_check()
        self.print_status()

        # Create orders and converge.
        self.place_orders()

    def print_status(self):
        """Print the current MM status."""
        pass
        #margin = self.exchange.get_margin()
        #position = self.exchange.get_position()
        #self.running_qty = self.exchange.get_delta()
        #tickLog = self.exchange.get_instrument()['tickLog']
        #self.start_XBt = margin["marginBalance"]

        #logger.info("Current XBT Balance: %.6f" % XBt_to_XBT(self.start_XBt))
        #logger.info("Current Contract Position: %d" % self.running_qty)
        #if settings.CHECK_POSITION_LIMITS:
        #    logger.info("Position limits: %d/%d" % (settings.MIN_POSITION, settings.MAX_POSITION))
        #if position['currentQty'] != 0:
        #    logger.info("Avg Cost Price: %.*f" % (tickLog, float(position['avgCostPrice'])))
        #    logger.info("Avg Entry Price: %.*f" % (tickLog, float(position['avgEntryPrice'])))
        #logger.info("Contracts Traded This Run: %d" % (self.running_qty - self.starting_qty))
        #logger.info("Total Contract Delta: %.4f XBT" % self.exchange.calc_delta()['spot'])





    def get_ticker(self):
        ticker = self.exchange.get_ticker()

        # Set up our buy & sell positions as the smallest possible unit above and below the current spread
        # and we'll work out from there. That way we always have the best price but we don't kill wide
        # and potentially profitable spreads.
        #self.start_position_buy = float((ticker.bidPrice1)) + settings.TICKSIZE
        # self.start_position_sell = float((ticker.askPrice1)) - settings.TICKSIZE
        self.start_position_buy = float((ticker.bidPrice1))
        self.start_position_sell = float((ticker.askPrice1))

        # If we're maintaining spreads and we already have orders in place,
        # make sure they're not ours. If they are, we need to adjust, otherwise we'll
        # just work the orders inward until they collide.
        if settings.MAINTAIN_SPREADS:
            if float(ticker.bidPrice1) == float(self.exchange.get_highest_buy()['price']):
                self.start_position_buy = float(ticker.bidPrice1)
            if float(ticker.askPrice1) == float(self.exchange.get_lowest_sell()['price']):
                self.start_position_sell = float(ticker.askPrice1)

        # Back off if our spread is too small.
        if self.start_position_buy * (1.00 + settings.MIN_SPREAD) > self.start_position_sell:
            self.start_position_buy *= (1.00 - (settings.MIN_SPREAD / 2))
            self.start_position_sell *= (1.00 + (settings.MIN_SPREAD / 2))

        #keep the spread exactly as MIN_SPREAD
        #self.start_position_buy = (self.start_position_sell + self.start_position_buy)/2 * (1-settings.MIN_SPREAD/2)
        #self.start_position_sell = (self.start_position_sell+ self.start_position_buy)/2 *(1+ settings.MIN_SPREAD/2)
        return ticker

        # Yifei
        # ticklog: digit, number of ticker price and position
        # tickLog = self.exchange.get_instrument()['tickLog']


        #self.start_position_buy = ticker.bidPrice1 + self.instrument['tickSize']
        # self.start_position_sell = ticker.askPrice1 - self.instrument['tickSize']

        #            if ticker['buy'] == self.exchange.get_highest_buy()['price']:
        #                self.start_position_buy = ticker["buy"]
        #            if ticker['sell'] == self.exchange.get_lowest_sell()['price']:
        #                self.start_position_sell = ticker["sell"]

        #Yifei
        #Not used
        # Midpoint, used for simpler order placement.
        #self.start_position_mid = ticker["mid"]

        #Yifei, Comment out temporily due to ticklog is not available in okex
        #logger.info(
        #    "%s Ticker: Buy: %.*f, Sell: %.*f" %
        #    (self.instrument['symbol'], tickLog, ticker["buy"], tickLog, ticker["sell"])
        #)
        #logger.info('Start Positions: Buy: %.*f, Sell: %.*f, Mid: %.*f' %
        #            (tickLog, self.start_position_buy, tickLog, self.start_position_sell,
        #             tickLog, self.start_position_mid))


    def get_price_offset(self, index):
        """Given an index (1, -1, 2, -2, etc.) return the price for that side of the book.
           Negative is a buy, positive is a sell."""
        # Maintain existing spreads for max profit
        if settings.MAINTAIN_SPREADS:
            start_position = self.start_position_buy if index < 0 else self.start_position_sell
            # First positions (index 1, -1) should start right at start_position, others should branch from there
            index = index + 1 if index < 0 else index - 1
        else:
            # Yifei
            # Coding error?
            # Offset mode: ticker comes from a reference exchange and we define an offset.
            start_position = self.start_position_buy if index < 0 else self.start_position_sell

            # If we're attempting to sell, but our sell price is actually lower than the buy,
            # move over to the sell side.
            if index > 0 and start_position < self.start_position_buy:
                start_position = self.start_position_sell
            # Same for buys.
            if index < 0 and start_position > self.start_position_sell:
                start_position = self.start_position_buy

        return math.toNearest(start_position * (1 + settings.INTERVAL) ** index, settings.TICKSIZE)

    ###
    # Orders
    ###

    def place_orders(self):
        """Create order items for use in convergence."""

        buy_orders = []
        sell_orders = []
        # Create orders from the outside in. This is intentional - let's say the inner order gets taken;
        # then we match orders from the outside in, ensuring the fewest number of orders are amended and only
        # a new order is created in the inside. If we did it inside-out, all orders would be amended
        # down and a new order would be created at the outside.
        for i in reversed(range(1, settings.ORDER_PAIRS + 1)):
            if not self.long_position_limit_exceeded():
                buy_orders.append(self.prepare_order(-i))
            if not self.short_position_limit_exceeded():
                sell_orders.append(self.prepare_order(i))

        return self.converge_orders(buy_orders, sell_orders)

    def prepare_order(self, index):
        """Create an order object."""

        if settings.RANDOM_ORDER_SIZE is True:
            quantity = random.randint(settings.MIN_ORDER_SIZE, settings.MAX_ORDER_SIZE)
        else:
            quantity = settings.ORDER_START_SIZE + ((abs(index) - 1) * settings.ORDER_STEP_SIZE)

        price = self.get_price_offset(index)

        return {'price': price, 'orderQty': quantity, 'side': "Buy" if index < 0 else "Sell"}



    def converge_orders(self, buy_orders, sell_orders):
        """Converge the orders we currently have in the book with what we want to be in the book.
           This involves amending any open orders and creating new ones if any have filled completely.
           We start from the closest orders outward."""

        #tickLog = self.exchange.get_instrument()['tickLog']
        #to_amend = []
        to_create = []
        to_cancel = []
        buys_matched = 0
        sells_matched = 0
        global timer
        existing_orders = self.exchange.get_orders()
        original_strategy = 0
        old_grid_strategy = 1

        if old_grid_strategy:
            # Check all existing orders and match them up with what we want to place.
            # If there's an open one, we might be able to amend it to fit what we want.
            for order in existing_orders:
                try:
                    if order.direction == DIRECTION_LONG:
                        desired_order = buy_orders[buys_matched]
                        buys_matched += 1
                    elif order.direction == DIRECTION_SHORT:
                        desired_order = sell_orders[sells_matched]
                        sells_matched += 1
                    else:
                        logger.error("Order direction is wrong!")

                        # Found an existing order. Do we need to amend it?
                        # if desired_order['orderQty'] != order.totalVolume - order.tradedVolume or (
                    #if (abs((desired_order['price'] / order.price) - 1) > settings.RELIST_INTERVAL):
                    if order.direction == DIRECTION_SHORT:
                        #if (abs((desired_order['price'] / order.price) - 1) > settings.RELIST_INTERVAL/10):
                        #if order.price == float(self.get_ticker().askPrice1) or order.price == float(self.get_ticker().askPrice2) or order.price == float(self.get_ticker().askPrice3):
                        if order.price == float(self.get_ticker().askPrice1):
                            logger.info("short order no change!")
                        else:
                            to_create.append({'orderQty': desired_order['orderQty'],
                                              'price': desired_order['price'], 'side': desired_order['side']})
                            to_cancel.append(order)
                    else:
#                        if order.price == float(self.get_ticker().bidPrice1) or order.price == float(
#                                self.get_ticker().bidPrice2) or order.price == float(self.get_ticker().bidPrice3):
                        if order.price == float(self.get_ticker().bidPrice1):

                            logger.info("bid order no change!")
                        else:
                        #if (abs((desired_order['price'] / order.price) - 1) > settings.RELIST_INTERVAL/10):

                            to_create.append({'orderQty': desired_order['orderQty'],
                                              'price': desired_order['price'], 'side': desired_order['side']})
                            to_cancel.append(order)
                except IndexError:
                    # Will throw if there isn't a desired order to match. In that case, cancel it.
                    logger.info("Should we cancel this order?")
                    to_cancel.append(order)

            while buys_matched < len(buy_orders):
                to_create.append(buy_orders[buys_matched])
                logger.info("to_create buy: %d %d" % (buys_matched, len(buy_orders)))
                buys_matched += 1


            while sells_matched < len(sell_orders):
                to_create.append(sell_orders[sells_matched])
                logger.info("to_create sell: %d %d" % (sells_matched, len(sell_orders)))
                sells_matched += 1

        elif original_strategy:
            # Check all existing orders and match them up with what we want to place.
            # If there's an open one, we might be able to amend it to fit what we want.
            for order in existing_orders:
                try:
                    if order.direction == DIRECTION_LONG:
                        desired_order = buy_orders[buys_matched]
                        buys_matched += 1
                    elif order.direction == DIRECTION_SHORT:
                        desired_order = sell_orders[sells_matched]
                        sells_matched += 1
                    else:
                        logger.error("Order direction is wrong!")

                    # Found an existing order. Do we need to amend it?
                    #if desired_order['orderQty'] != order.totalVolume - order.tradedVolume or (
                    #if (
                            # If price has changed, and the change is more than our RELIST_INTERVAL, amend.
                    #        desired_order['price'] != order.price and
                    #        abs((desired_order['price'] / order.price) - 1) > settings.RELIST_INTERVAL):
                    if (desired_order['price'] != order.price and len(existing_orders) ==2 ):
                        to_create.append({'orderQty': desired_order['orderQty'],
                                         'price': desired_order['price'], 'side': desired_order['side']})
                        to_cancel.append(order)

    #                if desired_order['orderQty'] != order['leavesQty'] or (
                            # If price has changed, and the change is more than our RELIST_INTERVAL, amend.
    #                        desired_order['price'] != order['price'] and
    #                        abs((desired_order['price'] / order['price']) - 1) > settings.RELIST_INTERVAL):
    #                    to_amend.append({'orderID': order['orderID'], 'orderQty': order['cumQty'] + desired_order['orderQty'],
    #                                     'price': desired_order['price'], 'side': order['side']})


                except IndexError:
                    # Will throw if there isn't a desired order to match. In that case, cancel it.
                    logger.info("Should we cancel this order?")
                    to_cancel.append(order)

            while buys_matched < len(buy_orders):
                to_create.append(buy_orders[buys_matched])
                logger.info("to_create buy: %d %d" % (buys_matched, len(buy_orders)))
                buys_matched += 1


            while sells_matched < len(sell_orders):
                to_create.append(sell_orders[sells_matched])
                logger.info("to_create sell: %d %d" % (sells_matched, len(sell_orders)))
                sells_matched += 1
        elif len(existing_orders) == 0:
            for order in buy_orders:
                to_create.append(order)
            for order in sell_orders:
                to_create.append(order)
            if timer != None:

                timer.cancel()
                logger.info("timer triggered, cancel all orders.")
            timer = threading.Timer(60 * 60, self.exchange.cancel_all_orders)
            timer.start()

        #if len(to_amend) > 0:
        #    for amended_order in reversed(to_amend):
        #        reference_order = [o for o in existing_orders if o.orderID == amended_order['orderID']][0]
        #        logger.info("Amending %4s: %d @ %.f to %d @ %.f (%+.f)" % (
        #            amended_order['side'],
        #            reference_order.totalVolume-reference_order.tradedVolume, reference_order.price,
        #            (amended_order['orderQty'] - reference_order.tradedVolume), amended_order['price'],
        #            (amended_order['price'] - reference_ordLast 2 Days2+ Days
#er.price)
        #        ))

                #reference_order = [o for o in existing_ordeLast 2 Days2+ Days
#rs if o['orderID'] == amended_order['orderID']][0]
                #logger.info("Amending %4s: %d @ %.*f to %d @ %.*f (%+.*f)" % (
                #    amended_order['side'],
                #    reference_order['leavesQty'], tickLog, reference_order['price'],
                #    (amended_order['orderQty'] - reference_order['cumQty']), tickLog, amended_order['price'],
                #    tickLog, (amended_order['price'] - reference_order['price'])
                #))
            # This can fail if an order has closed in the time we were processing.
            # The API will send us `invalid ordStatus`, which means that the order's status (Filled/Canceled)
            # made it not amendable.
            # If that happens, we need to catch it and re-tick.
        #    try:
        #        self.exchange.amend_bulk_orders(to_amend)
        #    except requests.exceptions.HTTPError as e:
        #        errorObj = e.response.json()
        #        if errorObj['error']['message'] == 'Invalid ordStatus':
        #            logger.warn("Amending failed. Waiting for order data to converge and retrying.")
        #            sleep(0.5)
        #            return self.place_orders()
        #        else:
        #            logger.error("Unknown error on amend: %s. Exiting" % errorObj)
        #            sys.exit(1)

        if len(to_create) > 0:
            logger.info("Creating %d orders:" % (len(to_create)))
            for order in reversed(to_create):
                logger.info("%4s %d @ %f" % (order['side'], order['orderQty'], order['price']))
                #logger.info("%4s %d @ %.*f" % (order['side'], order['orderQty'], tickLog, order['price']))
            self.exchange.create_bulk_orders(to_create)

        # Could happen if we exceed a delta limit
        if len(to_cancel) > 0:
            logger.info("Canceling %d orders:" % (len(to_cancel)))
            for order in reversed(to_cancel):
                logger.info("%4s %d @ %f" % (order.direction, order.totalVolume-order.tradedVolume, order.price))
                #logger.info("%4s %d @ %.*f" % (order['side'], order['leavesQty'], tickLog, order['price']))
            self.exchange.cancel_bulk_orders(to_cancel)

    ###
    # Position Limits
    ###

    def short_position_limit_exceeded(self):
        """Returns True if the short position limit is exceeded"""
        if not settings.CHECK_POSITION_LIMITS:
            return False
        position = self.exchange.get_delta()
        return position <= settings.MIN_POSITION

    def long_position_limit_exceeded(self):
        """Returns True if the long position limit is exceeded"""
        if not settings.CHECK_POSITION_LIMITS:
            return False
        position = self.exchange.get_delta()
        return position >= settings.MAX_POSITION

    ###
    # Sanity
    ##

    def sanity_check(self):
    #    """Perform checks before placing orders."""

        # Check if OB is empty - if so, can't quote.
    #    self.exchange.check_if_orderbook_empty()

        # Ensure market is still open.
    #    self.exchange.check_market_open()

        # Get ticker, which sets price offsets and prints some debugging info.
        ticker = self.get_ticker()

        # Sanity check:
        if self.get_price_offset(-1) >= float(ticker.askPrice1) or self.get_price_offset(1) <= float(ticker.bidPrice1):
            logger.error("Buy: %s, Sell: %s" % (self.start_position_buy, self.start_position_sell))
            logger.error("First buy position: %s\nOKEX Best Ask: %s\nFirst sell position: %s\nOKEX Best Bid: %s" %
                         (self.get_price_offset(-1), ticker.askPrice1, self.get_price_offset(1), ticker.bidPrice1))
            logger.error("Sanity check failed, exchange data is inconsistent")
            #self.exit()

        #if self.get_price_offset(-1) >= ticker["sell"] or self.get_price_offset(1) <= ticker["buy"]:
        #    logger.error("Buy: %s, Sell: %s" % (self.start_position_buy, self.start_position_sell))
        #    logger.error("First buy position: %s\nBitMEX Best Ask: %s\nFirst sell position: %s\nBitMEX Best Bid: %s" %
        #                 (self.get_price_offset(-1), ticker["sell"], self.get_price_offset(1), ticker["buy"]))
        #    logger.error("Sanity check failed, exchange data is inconsistent")
        #    self.exit()  # Messaging if the position limits are reached


        if self.long_position_limit_exceeded():
            logger.info("Long delta limit exceeded")
            logger.info("Current Position: %.f, Maximum Position: %.f" %
                        (self.exchange.get_delta(), settings.MAX_POSITION))

        if self.short_position_limit_exceeded():
            logger.info("Short delta limit exceeded")
            logger.info("Current Position: %.f, Minimum Position: %.f" %
                        (self.exchange.get_delta(), settings.MIN_POSITION))

    ###
    # Running
    ###

    #def check_file_change(self):
    #    """Restart if any files we're watching have changed."""
    #    for f, mtime in watched_files_mtimes:
    #        if getmtime(f) > mtime:
    #            self.restart()

    def check_connection(self):
        """Ensure the WS connections are still open."""
        return self.exchange.is_open()

    def exit(self):
        logger.info("Shutting down. All open orders will be cancelled.")
        try:
            self.exchange.cancel_all_orders()
            #self.exchange.bitmex.exit()
        except errors.AuthenticationError as e:
            logger.info("Was not authenticated; could not cancel orders.")
        except Exception as e:
            logger.info("Unable to cancel orders: %s" % e)

        sys.exit()

    def run_loop(self):
        while True:

            #Yifei
            #sys.stdout.write("-----\n")

            #sys.stdout.flush()

            #self.check_file_change()
            #sleep(settings.LOOP_INTERVAL)

            # This will restart on very short downtime, but if it's longer,
            # the MM will crash entirely as it is unable to connect to the WS on boot.
            if not self.check_connection():
                logger.error("Realtime data connection unexpectedly closed, Waiting for reconnection")
                #self.restart()
                sleep(settings.LOOP_INTERVAL)

            else:
                self.sanity_check()  # Ensures health of mm - several cut-out points here
                self.print_status()  # Print skew, delta, etc
                self.place_orders()  # Creates desired orders and converges to existing orders
                #self.grid_main()

    def grid_price(self,level):
        return self.basePrice * (1 + INTERVAL) ** (level - GRID_LEVELS / 2)

    def grid_place_order(self,order_type, level):

        try:
            #logger.info("grid_place_order level %d, grid[level] %s" % (level, grid[level]))
            if 0 <= level < GRID_LEVELS:
                price = self.grid_price(level)
#                logger.info("grid_place_order : level %d, price %f, direction %s" % (level, price, order_type))

                if (grid[level] == "" or grid[level] == "-"):

                    req = VtOrderReq()
                    req.symbol = self.exchange.symbol
                    req.volume = TRANCHE_SIZE
                    req.price = price
                    req.priceType = PRICETYPE_LIMITPRICE

                    if order_type == 'buy' and self.exchange.mainengine.dataEngine.positionDict['btc'].position - self.exchange.mainengine.dataEngine.positionDict['btc'].frozen> TRANCHE_SIZE*self.basePrice :
                        req.direction = DIRECTION_LONG
                        id = self.exchange.place_order(req)
                    elif order_type == 'sell' and self.exchange.mainengine.dataEngine.positionDict['eth'].position-self.exchange.mainengine.dataEngine.positionDict['eth'].frozen > TRANCHE_SIZE:
                        req.direction = DIRECTION_SHORT
                        id = self.exchange.place_order(req)
                    else:
                        id = ""
                        logger.error("insufficent money!Create_bulk_orders: Order direction is worng!")
                else:
                    logger.info("placing order on wrong level!")
                    #print out grid
                    self.grid_debug()
                    id = ""
            else:
                id = ""

        except Exception, e:
            id = ""
            print e

        grid[level] = id
        sleep(2)
        logger.info("grid_place_order level %d, grid[level] %s id %s" % (level, grid[level],id))

    def grid_debug(self):
        i = GRID_LEVELS - 1
        while i >= 0:
            if grid[i] == "" or grid [i] == "-":
                logger.info("grid %d, index %s"  % (i, grid[i]))
            else:
                for key,order in self.exchange.mainengine.dataEngine.orderDict.items():

                    if grid[i] == order.vtOrderID:
                        logger.info("grid %d, index %s price %f direction %s status %s"  % (i, grid[i], order.price, order.direction, order.status))


            i = i - 1


    def grid_init(self):

        ticker = self.exchange.get_ticker()

        self.basePrice = float(ticker.askPrice1)

        self.last_level = int(GRID_LEVELS / 2)
        logger.info("basePrice : %f, last_level :%d" %(self.basePrice,self.last_level))
        #Yifei, hardcoded, needs to be optimized
        for n in reversed(range(self.last_level - 1, -1, -1)):
            self.grid_place_order("buy", n)
        for n in range(self.last_level + 1, GRID_LEVELS):
            self.grid_place_order("sell", n)

        self.grid_debug()
    def grid_main(self):
        # loop forever
        #while True:
            # attempt to retrieve order history from matcher
        try:
            #    history = BLACKBOT.getOrderHistory(PAIR)
            history = self.exchange.mainengine.getAllOrders()
        except Exception as e:
            print e
            history = []
        try:
            if history:
                # loop through all grid levels
                # first all ask levels from the lowest ask to the highest -> range(grid.index("") + 1, len(grid))
                # then all bid levels from the highest to the lowest -> range(grid.index("") - 1, -1, -1)
                for n in list(range(self.last_level + 1, len(grid))) + list(range(self.last_level - 1, -1, -1)):

                    # find the order with id == grid[n] in the history list
                    for item in history:
                            if item.vtOrderID == grid[n]:
                                #logger.info("n: %d, grid[n]:%s" % (n, grid[n]))
                                order = item
                                #order = [item for item in history if item.vtOrderID == grid[n]]
                                status = order.status if order else ""
                                if status == STATUS_ALLTRADED:
                                    # BLACKBOT.deleteOrderHistory(PAIR)
                                    ticker = self.exchange.get_ticker()
                                    last_price = ticker.lastPrice
                                    grid[n] = ""
                                    self.last_level = n
                                    filled_price = float(order.price)
                                    filled_type = order.direction
                                    # log("## [%03d] %s%-4s Filled %18.*f%s" % (n, COLOR_BLUE, filled_type.upper(), PAIR.asset2.decimals, float(filled_price) / 10 ** PAIR.asset2.decimals, COLOR_RESET))

                                    logger.info("## [%d] Filled,filled price %f, filled_type %s, last price %f" % (n,filled_price, filled_type,last_price))
                                    self.grid_debug()
                                    if filled_type == DIRECTION_LONG:
                                        logger.info("filled_type == DIRECTION_LONG")
                                        #if filled_price >= last_price:
                                        if 1:
                                            self.grid_place_order("sell", n + 1)

                                        else:
                                            self.grid_place_order("buy", n)
                                            #Yifei
                                            self.last_level = n + 1
                                    elif filled_type == DIRECTION_SHORT:
                                        logger.info("filled_type == DIRECTION_SHORT")
                                        #if filled_price <= last_price:
                                        if 1:
                                            self.grid_place_order("buy", n - 1)
                                        else:
                                            self.grid_place_order("sell", n)
                                            #Yifei
                                            self.last_level = n - 1

                                    logger.info("last_level:%d" %(self.last_level))
                                # attempt to place again orders for empty grid levels or cancelled orders
                                #elif (status == "" or status == "Cancelled") and grid[n] != "-":
                                elif (status == "" or status == "Cancelled") and grid[n] != "-":
                                    grid[n] = ""
                                    if n > self.last_level:
                                        self.grid_place_order("sell", n)
                                    elif n < self.last_level:
                                        self.grid_place_order("buy", n)
            sleep(5)
        except Exception as e:
            print e
                #def restart(self):
    #    logger.info("Restarting the market maker...")
    #    os.execv(sys.executable, [sys.executable] + sys.argv)

#
# Helpers
#


#def XBt_to_XBT(XBt):
#    return float(XBt) / constants.XBt_TO_XBT


#def cost(instrument, quantity, price):
#    mult = instrument["multiplier"]
#    P = mult * price if mult >= 0 else mult / price
#    return abs(quantity * P)


#def margin(instrument, quantity, price):
#    return cost(instrument, quantity, price) * instrument["initMargin"]


def run():

    #Yifei
    logger.info('Okex Market Maker Version: 1.0')

    om = OrderManager()
    # Try/except just keeps ctrl-c from printing an ugly stacktrace
    try:
        om.run_loop()
    except (KeyboardInterrupt, SystemExit):
        sys.exit()
