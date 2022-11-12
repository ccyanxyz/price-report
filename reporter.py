import csv
import ccxt
from datetime import datetime
from prettytable import PrettyTable

'''
fetch all symbols USDT pair, weekly kline

report:
    token, ath, atl, now, atl-pct, now-pct, 5-pct-target

sort by: atl-pct, now-pct
'''

#Color
R = "\033[0;31;40m" #RED
G = "\033[0;32;40m" # GREEN
Y = "\033[0;33;40m" # Yellow
B = "\033[0;34;40m" # Blue
N = "\033[0m" # Reset

class Reporter:

    def __init__(self):
        self.binance = ccxt.binance()
        self.timeframe = '1w'
        self.limit = None
        self.quote = 'USDT'
        self.blacklists = ['USD', 'DAI', 'DOWN', 'UP', 'BULL', 'BEAR', 'AUD', 'EUR', 'GBP', 'BKRW']
        self.watchlist = [
                'BTC', 'ETH', 'DYDX', 'DOGE', 'ATOM', 'APT', 'MATIC', 'ADA', 'OSMO', 'DOT', 'LINK', 'NEAR',
                'APE', 'FLOW', 'STG', 'UNI', 'SUSHI', 'FXS', 'BAL', 'CVX', 'AAVE', 'COMP'
                ]

    def extract_points(self, symbol, base):
        # (ath, atl, now, atl-pct, now-pct, 5-pct-target)
        klines = self.binance.fetch_ohlcv(symbol, self.timeframe, limit=self.limit)
        ath = klines[0][4]
        ath_time = klines[0][0] / 1000
        # each ohlcv candle is a list of [ timestamp, open, high, low, close, volume ]
        for item in klines:
            if item[4] > ath:
                ath = item[4]
                ath_time = item[0] / 1000
        atl = ath
        atl_time = ath_time
        for item in klines:
            if item[4] < atl and item[0] / 1000 > atl_time:
                atl = item[4]
                atl_time = item[0] / 1000
        now = klines[-1][4]
        atl_pct = (ath - atl) / ath
        now_pct = (ath - now) / ath
        five_pct_target = ath * 0.05
        # return (ath, ath_time, atl, atl_time, now, atl_pct, now_pct, 5_ptc_target)
        return {
            'token': base,
            'symbol': symbol,
            'ath': ath,
            'ath_time': datetime.fromtimestamp(ath_time).strftime('%Y-%m-%d'),
            'atl': atl,
            'atl_time': datetime.fromtimestamp(atl_time).strftime('%Y-%m-%d'),
            'now': now,
            'atl_pct': str(int(atl_pct * 10000) / 100) + '%',
            'now_pct': str(int(now_pct * 10000) / 100) + '%',
            'five_pct_target': five_pct_target,
        }

    def fetch_results(self):
        markets = self.binance.fetch_markets()
        print('total markets:', len(markets))
        results = []
        watchlists = []
        for market in markets:
            if self.quote not in market['symbol']:
                continue
            if market['base'] in self.blacklists:
                continue
            if 'USD' in market['base']:
                continue
            if 'BULL' in market['base'] or 'BEAR' in market['base'] or 'DOWN' in market['base'] or 'UP' in market['base']:
                continue
            info = self.extract_points(market['symbol'], market['base'])
            results.append(info)
            if market['base'] in self.watchlist:
                watchlists.append(info)
        print('USDT markets:', len(results))
        results = sorted(results, key=lambda item: item['atl_pct'])
        results1 = sorted(results, key=lambda item: item['now_pct'])
        watchlists = sorted(watchlists, key=lambda item: item['now_pct'])
        return (results, results1, watchlists)

    def write_to_csv(self, filename, data):
        with open(filename, 'w') as f:
            fieldnames = ['token', 'symbol', 'ath', 'ath_time', 'atl', 'atl_time', 'now', 'atl_pct', 'now_pct', 'five_pct_target']
            writer = csv.DictWriter(f, fieldnames = fieldnames)
            writer.writeheader()
            for row in data:
                writer.writerow(row)

    def report(self):
        (ret_by_atl, ret_by_now, watch) = self.fetch_results()
        self.write_to_csv('data/sort_by_atl_pct.csv', ret_by_atl)
        self.write_to_csv('data/sort_by_now_pct.csv', ret_by_now)
        self.write_to_csv('data/watch_by_atl_pct.csv', watch)
        self.print(ret_by_now)
        self.print(watch)

    def print(self, data):
        table = PrettyTable()
        table.field_names = ['Token', 'ATH/time', 'ATL/time', 'NOW', 'ATL PCT', 'NOW PCT', '5 PCT TARGET']
        for item in data:
            row = [
                item['token'], str(item['ath']) + '(' + item['ath_time'] + ')',
                str(item['atl']) + '(' + item['atl_time'] + ')', item['now'],
                item['atl_pct'], item['now_pct'], item['five_pct_target']
            ]
            if item['five_pct_target'] >= item['now']:
                row[0] = G + row[0] + N
                row[-2] = G + row[-2] + N
            table.add_row(row)
        print(table)


if __name__ == '__main__':
    reporter = Reporter()
    reporter.report()
