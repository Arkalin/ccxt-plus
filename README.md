# CCXT-Plus

**CCXT-Plus** 是一个基于 [CCXT](https://github.com/ccxt/ccxt) 的扩展，旨在进一步简化获取量化数据的代码量，帮助开发者更高效地进行量化交易相关的开发。

## 特性

- 基于 CCXT 的二次封装，保留了原始功能的强大灵活性。
- 基于配置文件与约定，提供更简洁的接口，减少获取数据所需的代码量。
- 模块化，易于扩展和定制。
- 多线程与失败自动重试。
- 允许加载socks5代理并在数据获取时使用随机代理，大幅提高数据获取速度。
- 经测试获取binance btc 1m所有蜡烛图并保存为csv最快需要2分钟。

## 使用

```bash
git clone https://github.com/Arkalin/ccxt-plus.git
```

## 快速开始

以下是使用 CCXT-Plus 获取binance蜡烛图的简单示例：

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

## 注意

尚为早期开发版本，目前经过可用性测试的仅有binance交易所的fetch_all_ohlcv和fetch_all_funding_rate_history

## 文档

有关更多信息，请参考以下文档：

- [CCXT 官方文档](https://docs.ccxt.com/)
- CCXT-Plus 文档（待补充）

## 贡献

欢迎对本项目的改进和扩展！如果您有任何建议或发现问题，请提交 Issue 或 Pull Request。

## 许可证

CCXT-Plus 遵循 MIT 许可证。

---
