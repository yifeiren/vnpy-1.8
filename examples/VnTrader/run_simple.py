# encoding: UTF-8

# 重载sys模块，设置默认字符串编码方式为utf8
import sys
import thread


sys.path.append("/root/vnpy-1.8/examples/VnTrader/Arbitrage")
reload(sys)
sys.setdefaultencoding('utf8')

# 判断操作系统
import platform
import threading

system = platform.system()

# vn.trader模块
from vnpy.event import EventEngine
from vnpy.trader.vtEngine import MainEngine
from vnpy.trader.uiQt import createQApp
from vnpy.trader.uiMainWindow import MainWindow
from triangular_arbitrage import *

# 加载底层接口
#Yifei from vnpy.trader.gateway import ctpGateway
from vnpy.trader.gateway import okexGateway


# 加载上层应用
#from vnpy.trader.app import (riskManager, ctaStrategy, spreadTrading)

connected_sig = threading.Event()


# ----------------------------------------------------------------------
def main():
    """主程序入口"""
    # 创建Qt应用对象
#    qApp = createQApp()

    # 创建事件引擎
    ee = EventEngine()

    # 创建主引擎
    me = MainEngine(ee)

    # 添加交易接口
    me.addGateway(okexGateway)

    # 添加上层应用
 #   me.addApp(riskManager)
 #   me.addApp(ctaStrategy)
 #   me.addApp(spreadTrading)

    # 创建主窗口
    #mw = MainWindow(me, ee)
    #mw.showMaximized()
#Yifei
    #exchange = {
    #    'exchange': 'bittrex',
    #    'keyFile': '../keys/bittrex.key',
    #    'tickerPairA': 'BTC-ETH',
    #    'tickerPairB': 'ETH-LTC',
    #    'tickerPairC': 'BTC-LTC',
    #    'tickerA': 'BTC',
    #    'tickerB': 'ETH',
    #    'tickerC': 'LTC'
    #}

    try:


        exchange = {
            'tickerPairA': 'ltc_eth',
            'tickerPairB': 'eth_btc',
            'tickerPairC': 'ltc_btc',
            'tickerA': 'ltc',
            'tickerB': 'eth',
            'tickerC': 'btc'
        }


        engine = CryptoEngineTriArbitrage(me, exchange, connected_sig,True)

        me.getGateway('OKEX').set_event(connected_sig)

        #t=threading.Thread(target=engine.run)
        #t.start()

        exchange = {
            'tickerPairA': 'gnx_eth',
            'tickerPairB': 'eth_btc',
            'tickerPairC': 'gnx_btc',
            'tickerA': 'gnx',
            'tickerB': 'eth',
            'tickerC': 'btc'
        }

        engine = CryptoEngineTriArbitrage(me, exchange, connected_sig, True)

        me.getGateway('OKEX').set_event(connected_sig)

        #t = threading.Thread(target=engine.run)
        #t.start()

        exchange = {
            'tickerPairA': 'eos_eth',
            'tickerPairB': 'eth_btc',
            'tickerPairC': 'eos_btc',
            'tickerA': 'eos',
            'tickerB': 'eth',
            'tickerC': 'btc'
        }

        engine = CryptoEngineTriArbitrage(me, exchange, connected_sig, True)

        me.getGateway('OKEX').set_event(connected_sig)

        #t = threading.Thread(target=engine.run)
        #t.start()

        exchange = {
            'tickerPairA': 'hpb_eth',
            'tickerPairB': 'eth_btc',
            'tickerPairC': 'hpb_btc',
            'tickerA': 'hpb',
            'tickerB': 'eth',
            'tickerC': 'btc'
        }

        engine = CryptoEngineTriArbitrage(me, exchange, connected_sig,False)
        me.getGateway('OKEX').set_event(connected_sig)

        t=threading.Thread(target=engine.run)
        t.start()

        #thread.start_new_thread(engine.run, ())
        # 在主线程中启动Qt事件循环
        me.getGateway('OKEX').connect()

    except Exception, e:
        # raise
        print e
 #   sys.exit(qApp.exec_())


if __name__ == '__main__':
    main()
