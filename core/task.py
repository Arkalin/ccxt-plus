from time import sleep
from helpers.config import Config
from helpers.utils import DataFlag


class Task:
    """
    A class representing a task for processing data using multiple threads and retry logic.

    Attributes:
        timestamp_list (list): List of generated timestamps for task execution.
        online_worker_count (int): Number of online workers.
        local_worker_count (int): Number of local workers.
        _initialize_func (callable): A function to initialize the task.
    """

    def __init__(self, since, until, thread_count, fetch_func, map_func=None):
        """
        Initialize the Task object.

        Args:
            since (int): Start timestamp for the task.
            until (int): End timestamp for the task.
            thread_count (int): Total number of threads to use.
            fetch_func (callable): Function to fetch raw data.
            map_func (callable, optional): Function to map raw data. Defaults to None.
        """
        self.timestamp_list = None
        self.online_worker_count = None
        self.local_worker_count = None
        self._initialize_func = None
        self._build_initialize_func(since, until, thread_count, fetch_func, map_func)

    def _build_initialize_func(self, since, until, thread_count, fetch_func, map_func):
        """
        Build the initialization function for the task.

        Args:
            since (int): Start timestamp for the task.
            until (int): End timestamp for the task.
            thread_count (int): Total number of threads to use.
            fetch_func (callable): Function to fetch raw data.
            map_func (callable, optional): Function to map raw data. Defaults to None.
        """

        def initialize_func():
            """
            Initialize the task by fetching data and determining timestamps.

            Raises:
                RuntimeError: If the task cannot be initialized after maximum attempts.
            """
            nonlocal since
            online_worker_count = thread_count
            local_worker_count = max(1, thread_count // Config("LOCAL_THREADS_RATIO"))
            test_since = since
            attempt_times = Config("MAX_ATTEMPT_TIMES")
            while attempt_times:
                test_raw_data, flag = fetch_func(since=test_since)
                test_data = (
                    map_func(test_raw_data) if callable(map_func) else test_raw_data
                )
                if flag == DataFlag.NORMAL and len(test_data) > 0:
                    delta = abs(test_data[0][0] - test_data[-1][0])
                    since = test_data[0][0]
                    timestamp_list = list(range(since, until, delta))
                    self.timestamp_list = timestamp_list
                    self.online_worker_count = online_worker_count
                    self.local_worker_count = local_worker_count
                    return self
                else:
                    attempt_times -= 1
                    sleep(1)
            raise RuntimeError("Failed to generate task, maximum attempts exhausted")

        self._initialize_func = initialize_func

    def initialize(self):
        """
        Execute the initialization function if callable.

        Returns:
            Task: The initialized task instance.

        Raises:
            RuntimeError: If the initialization fails.
        """
        if callable(self._initialize_func):
            return self._initialize_func()
        raise RuntimeError("Task initialzing failed, _initialize_func is not callable")
