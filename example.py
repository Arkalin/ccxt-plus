import ccxt.binance
from helpers.proxy import ProxyManager
from wrapper import CCXTExchangeWrapper
from core.mapper import VolumeMapper
import ccxt

if __name__ == "__main__":
    binance = ccxt.binance()
    binance_future = ccxt.binance()
    binance_future.options["defaultType"] = "future"
    wrapper = CCXTExchangeWrapper(binance)
    wrapper_future = CCXTExchangeWrapper(binance_future)

    with open("pairs.txt", "r") as infile:
        symbols = infile.read().splitlines()
    timeframes = ["1m","15m"]

    count = 0
    total = len(symbols)
    with ProxyManager():
        for symbol in symbols:
            for timeframe in timeframes:
                wrapper_future.fetch_all_ohlcv(symbol, timeframe,mapper = VolumeMapper)
                wrapper.fetch_all_ohlcv(symbol, timeframe,mapper = VolumeMapper)
            count += 1
            print(f"\n--------------{count}/{total}------------------\n")