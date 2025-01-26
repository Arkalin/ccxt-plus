# CCXT-Plus

**CCXT-Plus** is an extension based on [CCXT](https://github.com/ccxt/ccxt), aimed at further simplifying the code required to obtain quantitative data, helping developers to develop quantitative trading more efficiently.

## Features

- Secondary encapsulation based on CCXT, retaining the powerful flexibility of the original functions.
- Provides a simpler interface based on configuration files and conventions, reducing the amount of code required to obtain data.
- Modular, easy to extend and customize.
- Multithreading and automatic retry on failure.
- Allows loading socks5 proxy and using random proxies when fetching data, greatly improving data fetching speed.
- Tested to fetch all Binance BTC 1m candlesticks and save as CSV in as fast as 2 minutes.

## Usage

```bash
git clone https://github.com/Arkalin/ccxt-plus.git
```

## Quick Start

Here is a simple example of using CCXT-Plus to fetch Binance candlesticks:

```python
from wrapper import CCXTExchangeWrapper
import ccxt

binance = ccxt.binance()
wrapper = CCXTExchangeWrapper(binance)
wrapper.fetch_all_ohlcv("BTC/USDT", "15m")
```

```bash
2024-12-15 18:44:42,059 - INFO - [binance_spot_BTC-USDT_15m] Task started
2024-12-15 18:44:48,051 - INFO - Total 565 missing data points
2024-12-15 18:44:48,438 - INFO - Created File: data\binance\spot\BTC-USDT\15m\0.csv
2024-12-15 18:44:48,755 - INFO - Created File: data\binance\spot\BTC-USDT\15m\1.csv
2024-12-15 18:44:48,934 - INFO - Created File: data\binance\spot\BTC-USDT\15m\2.csv
2024-12-15 18:44:48,936 - CRITICAL - [binance_spot_BTC-USDT_15m] Task completed
```

## Note

This is an early development version, currently only the fetch_all_ohlcv and fetch_all_funding_rate_history of the Binance exchange have been tested for usability.

## Documentation

For more information, please refer to the following documents:

- [CCXT Official Documentation](https://docs.ccxt.com/)
- CCXT-Plus Documentation (to be added)

## Contribution

Improvements and extensions to this project are welcome! If you have any suggestions or find any issues, please submit an Issue or Pull Request.

## License

CCXT-Plus follows the MIT license.

---
