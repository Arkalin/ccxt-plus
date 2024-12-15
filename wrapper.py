from functools import partial
from time import time
import ccxt

from core.factory import Factory
from core.mapper import *
from core.saver import CSVSaver
from core.task import Task
from helpers.config import Config
from helpers.logger import Logger
from helpers.utils import DataFlag, Labels
from helpers.proxy import ProxyManager

_ACTIONS_MAPPING = {
    "DEFAULT": [
        "drop_duplicates",
        "sort",
        "save_missing_times",
        "fix_integrity",
        "drop_last",
        "transfer_time",
    ],
    "MODE_1": [
        "drop_duplicates",
        "sort",
        "drop_last",
        "transfer_time",
    ],
}


class CCXTExchangeWrapper:
    """
    A wrapper class for CCXT exchange objects, providing additional methods
    for fetching and processing data with multithreaded support and
    configurable actions.

    Attributes:
        exchange_obj (ccxt.Exchange): The CCXT exchange object.
    """

    def __init__(self, exchange_obj: ccxt.Exchange):
        """
        Initialize the wrapper with the given CCXT exchange object.

        Args:
            exchange_obj (ccxt.Exchange): The CCXT exchange object to wrap.
        """
        self.exchange_obj = exchange_obj

    def fetch_all_ohlcv(self, symbol: str, timeframe, **kwargs):
        """
        Wrapper for the fetch_ohlcv method.

        Args:
            symbol (str): The trading pair symbol, e.g., 'BTC/USDT'.
            timeframe (str): The timeframe for OHLCV data, e.g., '1h', '1d'.
            kwargs: Additional optional arguments:
            - `since` (int): Start timestamp (default: Config("DEFAULT_SINCE_TIME")).
            - `until` (int): End timestamp (default: current time).
            - `labels` (Labels): Custom labels for the task (default: auto-generated).
            - `threads` (int): Number of threads (default: Config("GLOBAL_THREADS")).
            - `mapper` (BaseMapper): Data mapper (default: OHLCVMapper).
            - `actions` (list): List of actions to perform (default: ["drop_duplicates","sort","save_missing_times","fix_integrity","drop_last","transfer_time"]).
        """
        labels = kwargs.get(
            "labels",
            Labels(
                self.exchange_obj.id,
                self.exchange_obj.options.get("defaultType"),
                symbol,
                timeframe,
            ),
        )
        fetch_func = self._ccxt_fetch_func_wrapper(
            partial(self.exchange_obj.fetch_ohlcv, symbol=symbol, timeframe=timeframe)
        )
        mapper: BaseMapper = kwargs.get("mapper", OHLCVMapper)
        task = Task(
            kwargs.get("since", Config("DEFAULT_SINCE_TIME")),
            kwargs.get("until", int(time() * 1000)),
            kwargs.get("threads", Config("GLOBAL_THREADS")),
            fetch_func,
        )
        saver = CSVSaver(
            labels,
            kwargs.get(
                "actions",
                _ACTIONS_MAPPING["DEFAULT"],
            ),
            mapper.columns,
            mapper.time_column_index,
            timeframe=timeframe,
        )
        factory = Factory(fetch_func)
        self._execute(labels, task, saver, factory, mapper.map_with_validation)

    def fetch_all_funding_rate_history(self, symbol: str, **kwargs):
        """
        Wrapper for the fetch_funding_rate_history method.

        Args:
            symbol (str): The trading pair symbol, e.g., 'BTC/USDT'.

            kwargs: Additional optional arguments:
            - `since` (int): Start timestamp (default: Config("DEFAULT_SINCE_TIME")).
            - `until` (int): End timestamp (default: current time).
            - `labels` (Labels): Custom labels for the task (default: auto-generated).
            - `threads` (int): Number of threads (default: Config("GLOBAL_THREADS")).
            - `mapper` (BaseMapper): Custom data mapper (default: FundingRateHistoryMapper).
            - `actions` (list): List of actions to perform (default: ["drop_duplicates","sort","drop_last","transfer_time"]).
        """
        labels = kwargs.get(
            "labels",
            Labels(
                self.exchange_obj.id,
                "funding_rate_history",
                symbol,
            ),
        )
        fetch_func = self._ccxt_fetch_func_wrapper(
            partial(self.exchange_obj.fetch_funding_rate_history, symbol=symbol)
        )
        mapper: BaseMapper = kwargs.get("mapper", FundingRateHistoryMapper)
        task = Task(
            kwargs.get("since", Config("DEFAULT_SINCE_TIME")),
            kwargs.get("until", int(time() * 1000)),
            kwargs.get("threads", Config("GLOBAL_THREADS")),
            fetch_func,
            map_func=mapper.map_with_validation,
        )
        actions = kwargs.get("actions", _ACTIONS_MAPPING["MODE_1"])
        saver = CSVSaver(labels, actions, mapper.columns, mapper.time_column_index)
        factory = Factory(fetch_func)
        self._execute(labels, task, saver, factory, map_func=mapper.map_with_validation)

    def _ccxt_fetch_func_wrapper(self, ccxt_fetch_func):
        """
        Wrap the CCXT fetch function to include proxy support and error handling.

        Args:
            ccxt_fetch_func (callable): The CCXT fetch function to wrap.

        Returns:
            callable: A wrapped function that uses a random proxy and handles exceptions.
        """

        def wrapped(*args, **kwargs):
            try:
                self.exchange_obj.proxies = ProxyManager.get_random_proxy()
                return ccxt_fetch_func(*args, **kwargs), DataFlag.NORMAL
            except Exception:
                return None, DataFlag.ERROR

        return wrapped

    @staticmethod
    def _execute(labels, task: Task, saver: CSVSaver, factory: Factory, map_func=None):
        """
        Execute the task using the provided components.

        Args:
            labels (Labels): Task labels for logging.
            task (Task): The task instance to execute.
            saver (CSVSaver): The saver instance to handle data storage.
            factory (Factory): The factory instance for task management.
            map_func (callable, optional): Function to map raw data. Default is None.

        Returns:
            bool: True if the task completes successfully.

        Raises:
            Exception: If any error occurs during execution.
        """
        Logger.info("Task started", prefix=labels)
        task.initialize()
        raw_data = factory.complete(task)
        data = map_func(raw_data) if callable(map_func) else raw_data
        saver.save(data)
        Logger.critical("Task completed", prefix=labels)
        return True
