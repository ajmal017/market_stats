import statistics
import math
from functools import lru_cache
from itertools import accumulate

import pygal

from lib import util
from lib.errors import *
import gcnv

class Pair:
    def __init__(self, ticker1, ticker2, fixed_stdev_ratio = None):
        self.ticker1 = ticker1
        self.ticker2 = ticker2
        self.fixed_stdev_ratio = fixed_stdev_ratio

    # -------- Correlation part -------

    @lru_cache(maxsize=None)
    def correlation(self, back_days):
        changes1, changes2 = self.parallel_percentage_changes(back_days)
        return (util.covariance(changes1, changes2)
                / (statistics.stdev(changes1) * statistics.stdev(changes2)))

    @lru_cache(maxsize=None)
    def beta(self, back_days):
        return self.correlation(back_days) * self.stdev_ratio(back_days)

    @lru_cache(maxsize=None)
    def stdev_ratio(self, back_days):
        if self.fixed_stdev_ratio != None:
            return self.fixed_stdev_ratio
        changes1, changes2 = self.parallel_percentage_changes(back_days)
        return (statistics.stdev(changes1) / statistics.stdev(changes2))

    # Gets the daily standard deviation of backdays and multiplies by sqrt of 
    # year days to get the aggregated value
    def hv(self, back_days):
        changes_metric = self.percentage_changes(back_days) # simple percentage change
        return statistics.stdev(changes_metric) * 15.8745 # = math.sqrt(252)

    @lru_cache(maxsize=None)
    def hv_to_10_ratio(self, back_days):
        return self.hv(back_days) / 10

    # -------- Pairs part ----------

    @lru_cache(maxsize=None)
    def parallel_closes(self, back_days):
        closes = gcnv.data_handler.list_data(
                    [["stock", self.ticker1], ["stock", self.ticker2]],
                    back_days)
        if len(closes) == 0:
            raise GettingInfoError(
                    f"No pairs data for {self.ticker1}-{self.ticker2}")
        return closes

    @lru_cache(maxsize=None)
    def parallel_percentage_changes(self, back_days):
        closes_ticker1, closes_ticker2 = self.parallel_closes(back_days)

        percentage_changes_ticker1 = []; percentage_changes_ticker2 = []
        for i in range(1, len(closes_ticker1)):
            percentage_changes_ticker1.append(
                    (closes_ticker1[i] / closes_ticker1[i-1] - 1) * 100)
            percentage_changes_ticker2.append(
                    (closes_ticker2[i] / closes_ticker2[i-1] - 1) * 100)

        return (percentage_changes_ticker1, percentage_changes_ticker2)

    # Calculates percentage changes taking the base from first day since back days.
    # Used mostly for charting
    @lru_cache(maxsize=None)
    def parallel_accumulative_percentage_changes(self, back_days):
        closes_ticker1, closes_ticker2 = self.parallel_closes(back_days)

        closes_ticker1_base = closes_ticker1[0]
        closes_ticker2_base = closes_ticker2[0]

        percentage_changes_ticker1 = [0] # starts with 0 change
        percentage_changes_ticker2 = [0] # starts with 0 change
        for i in range(1, len(closes_ticker1)):
            percentage_changes_ticker1.append(
                    (closes_ticker1[i] / closes_ticker1_base - 1) * 100)
            percentage_changes_ticker2.append(
                    (closes_ticker2[i] / closes_ticker2_base - 1) * 100)

        return (percentage_changes_ticker1, percentage_changes_ticker2)

    # Percentage changes of the pair as a whole
    @lru_cache(maxsize=None)
    def percentage_changes(self, back_days):
        percentage_changes1, percentage_changes2 = self.parallel_percentage_changes(back_days)
        percentage_changes = []
        positively_correlated = self.correlation(back_days) >= 0
        for i in range(len(percentage_changes1)):
            if positively_correlated:
                change = percentage_changes1[i] - percentage_changes2[i] * self.stdev_ratio(back_days)
            else:
                change = percentage_changes1[i] + percentage_changes2[i] * self.stdev_ratio(back_days)
            percentage_changes.append(change)
        return percentage_changes

    # Could also be called accumulative_percentage_changes
    # Sum of percentage changes of the pair as a whole
    @lru_cache(maxsize=None)
    def closes(self, back_days):
        return list(accumulate(self.percentage_changes(back_days)))

    def get_last_close(self, back_days):
        return self.closes(back_days)[-1]

    @lru_cache(maxsize=None)
    def ma(self, back_days):
        closes = self.closes(back_days)
        if len(closes) == 0:
            return None
        return statistics.mean(closes)

    @lru_cache(maxsize=None)
    def current_to_ma_diff(self, back_days):
        return self.get_last_close(back_days) - self.ma(back_days)

    @lru_cache(maxsize=None)
    def min(self, back_days):
        return min(self.closes(back_days))

    @lru_cache(maxsize=None)
    def max(self, back_days):
        return max(self.closes(back_days))

    def current_rank(self, back_days):
        return ((self.get_last_close(back_days) - self.min(back_days))
                    / (self.max(back_days) - self.min(back_days)) * 100)

    def output_chart(self, back_days):
        line_chart = pygal.Line(truncate_label=-1)
        line_chart.title = f"{self.ticker1}-{self.ticker2}"
        line_chart.x_title = (f"Ratio: {format(self.stdev_ratio(back_days), '.2f')} - "
                                f"Corr: {format(self.correlation(back_days), '.2f')}")
        x_labels = []
        for i in range(len(self.parallel_accumulative_percentage_changes(back_days)[0])):
            if i % 20 == 0:
                x_labels.append(i)
            else:
                x_labels.append('')
        x_labels.reverse()
        line_chart.x_labels = x_labels
        line_chart.add(str(back_days), self.closes(back_days))
        line_chart.add(self.ticker1, self.parallel_accumulative_percentage_changes(back_days)[0])
        line_chart.add(self.ticker2, self.parallel_accumulative_percentage_changes(back_days)[1])
        # line_chart.show_dots = False
        line_chart.render_to_file(f"{gcnv.store_dir}/{self.ticker1}-{self.ticker2}.svg")