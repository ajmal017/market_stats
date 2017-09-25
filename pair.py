from datetime import datetime, timedelta

from functools import lru_cache
from util import *
import statistics
import math

class Pair:
    def __init__(self, data_handler, ticker1, ticker2):
        self.data_handler = data_handler
        self.ticker1 = ticker1
        self.ticker2 = ticker2


    @lru_cache(maxsize=None)
    def correlation(self, back_days):
        changes = self.percentage_changes(back_days)
        return covariance(changes[0], changes[1]) / (statistics.stdev(changes[0]) * statistics.stdev(changes[1]))


    @lru_cache(maxsize=None)
    def beta(self, back_days):
        return self.correlation(back_days) * self.stdev_ratio(back_days)


    @lru_cache(maxsize=None)
    def stdev_ratio(self, back_days):
        changes = self.percentage_changes(back_days)
        return (statistics.stdev(changes[0]) / statistics.stdev(changes[1]))



    #private

    @lru_cache(maxsize=None)
    def percentage_changes(self, back_days):
        max_date_ticker1 = self.data_handler.get_max_stored_date("STOCK", self.ticker1)
        max_date_ticker2 = self.data_handler.get_max_stored_date("STOCK", self.ticker2)
        if max_date_ticker1 is None or max_date_ticker2 is None or max_date_ticker1 != max_date_ticker2:
            return ([], [])

        closes_ticker1 = []
        closes_ticker2 = []
        for i in range(back_days):
            older_date = max_date_ticker1 - timedelta(days = i)
            close_ticker1 = self.data_handler.find_in_data("STOCK", self.ticker1, older_date.strftime("%Y%m%d"), True)
            close_ticker2 = self.data_handler.find_in_data("STOCK", self.ticker2, older_date.strftime("%Y%m%d"), True)
            if close_ticker1 is not None and close_ticker2 is not None:
                closes_ticker1.append(close_ticker1)
                closes_ticker2.append(close_ticker2)

        percentage_changes_ticker1 = []
        percentage_changes_ticker2 = []

        for i in range(len(closes_ticker1)):
            if i == 0:
                continue
            percentage_changes_ticker1.append((closes_ticker1[i] / closes_ticker1[i-1] - 1) * 100)
            percentage_changes_ticker2.append((closes_ticker2[i] / closes_ticker2[i-1] - 1) * 100)

        return (percentage_changes_ticker1, percentage_changes_ticker2)