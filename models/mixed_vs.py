from functools import lru_cache
import statistics

import gcnv

class MixedVs:
    def __init__(self, iv, hv):
        self.iv = iv
        self.hv = hv
        self.ticker = self.iv.ticker
        assert self.iv.ticker == self.hv.ticker

    def iv_current_to_hv_average(self, date, back_days):
        return self.iv.get_at(date) / self.hv.period_average(back_days)

    def iv_average_to_hv_average(self, back_days):
        return self.iv.period_average(back_days) / self.hv.period_average(back_days)

    @lru_cache(maxsize=None)
    def iv_hv_difference(self, back_days):
        ivs, hvs = gcnv.data_handler.list_data(
                    [["iv", self.ticker], ["hv", self.ticker]], back_days)
        hvs = hvs[20:] # 20 because no trading days are already removed
        return [ivs[i] * 100 - hvs[i] * 100 for i in range(len(hvs))]

    # returns percentage of success of daily one month volatility trading
    def positive_difference_ratio(self, back_days):
        positive_count = sum(1 for diff in self.iv_hv_difference(back_days)
                                if diff > 0)
        return (positive_count / len(self.iv_hv_difference(back_days))) * 100

    def difference_average(self, back_days):
        return statistics.mean(self.iv_hv_difference(back_days))