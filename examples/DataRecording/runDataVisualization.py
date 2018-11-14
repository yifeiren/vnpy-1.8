# encoding: UTF-8

import multiprocessing
from time import sleep
from datetime import datetime, time

from vnpy.event import EventEngine2
from vnpy.trader.vtEvent import EVENT_LOG, EVENT_ERROR
from vnpy.trader.vtEngine import MainEngine, LogEngine
#from vnpy.trader.gateway import ctpGateway
from vnpy.trader.app import dataRecorder
from vnpy.trader.gateway import okexGateway


from datetime import datetime, timedelta
from collections import OrderedDict
from itertools import product
import multiprocessing
import copy

import pymongo
import numpy as np
import pandas as pd

import matplotlib.pyplot as plt

# 如果安装了seaborn则设置为白色风格
try:
    import seaborn as sns       
    sns.set_style('whitegrid')  
except ImportError:
    pass

from vnpy.trader.vtGlobal import globalSetting
from vnpy.trader.vtObject import VtTickData, VtBarData
from vnpy.trader.vtConstant import *
from vnpy.trader.vtGateway import VtOrderData, VtTradeData
from matplotlib.pylab import date2num
import datetime
import matplotlib.dates as mdates
import matplotlib.font_manager as font_manager


# ----------------------------------------------------------------------
def loadHistoryData(dbName,symbol,type, forecast = 0):
    """载入历史数据"""
    try:
        dbClient = pymongo.MongoClient(globalSetting['mongoHost'], globalSetting['mongoPort'])
        collection = dbClient[dbName][symbol]

        #output(u'开始载入数据')

        #flt = {'type': {'$eq': type}}
        d1 = datetime.datetime.now()
        d2 = d1 - datetime.timedelta(days=1)
        flt = {'futureindex':{'$eq':0}}
        #flt = {'buy': {'$eq': 0}}
        #flt = {'thisweekvsspot':{'$gt':1}}


        cx = collection.find(flt)

        for data in cx:
        # 获取时间戳对象
            #dt = data['datetime'].time()
            collection.delete_one(data)
            print u'删除无效数据，时间戳：%s' % data['datetime']

        if forecast ==0:
            flt = {'datetime': {'$gte': d2,
                                '$lt': d1},'type': {'$eq': type} }
        else:
            flt = {'datetime': {'$gte': d2,
                                '$lt': d1},'type': {'$eq': type}, 'forecast': {'$gt':0} }
        initCursor = collection.find(flt).sort('datetime')



        #data = pd.DataFrame(list(collection.find(flt).sort('datetime')))
        data = pd.DataFrame(list(collection.find(flt)))
        del data['_id']
        data = data[['datetime', 'buy', 'sell', 'type', 'nextweekvsthisweek', 'quartervsthisweek', 'quartervsnextweek', 'futureindex', 'forecast', 'thisweekvsspot']]
        return (data)
    except Exception,e:
        print e


def visualize():
    try:
        plt.ion()
        fig, (ax,ax2) = plt.subplots(2,sharex=True)
        ax.xaxis_date()

        #plt.show()

        while True:
            hist_data_type1 = loadHistoryData('VnTrader_Tick_Db', 'eos.OKEX', 1)
            hist_data_type2 = loadHistoryData('VnTrader_Tick_Db', 'eos.OKEX', 2)
            hist_data_type3 = loadHistoryData('VnTrader_Tick_Db', 'eos.OKEX', 3)
            hist_data_type4 = loadHistoryData('VnTrader_Tick_Db', 'eos.OKEX', 3,1)

            ax.clear()
            ax2.clear()
            ax.plot(hist_data_type1['datetime'],hist_data_type1['buy'], label='this_week')
            ax.plot(hist_data_type2['datetime'],hist_data_type2['buy'], label='next_week')
            ax.plot(hist_data_type3['datetime'],hist_data_type3['buy'], label='quarter')
            ax.plot(hist_data_type3['datetime'],hist_data_type3['futureindex'], label='futureindex')
            if hist_data_type4 != None:
                ax.plot(hist_data_type4['datetime'],hist_data_type4['forecast'], label='forecast')


            ax2.plot(hist_data_type3['datetime'],hist_data_type3['quartervsthisweek'], label='quarter/this week')
            ax2.plot(hist_data_type3['datetime'],hist_data_type3['quartervsnextweek'], label='quarter/next week')
            ax2.plot(hist_data_type1['datetime'],hist_data_type1['nextweekvsthisweek'], label='next week/this week')
            ax2.plot(hist_data_type1['datetime'],hist_data_type1['thisweekvsspot'], label='this week/spot')



            props = font_manager.FontProperties(size=10)
            leg = ax.legend(loc='upper left', shadow=True, fancybox=True, prop=props)
            leg.get_frame().set_alpha(0.5)

            xfmt = mdates.DateFormatter('%y-%m-%d %H:%M')
            ax.xaxis.set_major_formatter(xfmt)

            props = font_manager.FontProperties(size=10)
            leg = ax2.legend(loc='upper left', shadow=True, fancybox=True, prop=props)
            leg.get_frame().set_alpha(0.5)

            xfmt = mdates.DateFormatter('%y-%m-%d %H:%M')
            ax2.xaxis.set_major_formatter(xfmt)

            #plt.grid()
            plt.draw()
            plt.pause(300)
#            plt.plot()
#            plt.show()
            #sleep(1)

    except Exception,e:
        print e

if __name__ == '__main__':
    visualize()
