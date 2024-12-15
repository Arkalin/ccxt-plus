import queue
import threading

from core.task import Task
from helpers.config import Config
from helpers.utils import DataFlag

class Factory:
    """
    A factory class for managing tasks using a producer-consumer model. It handles
    fetching data, managing retry logic, and multithreaded processing.

    Attributes:
        fetch_data_callback (callable): A callback function to fetch data.
        max_attempts (int): Maximum retry attempts for fetching data.
        _online_queue (queue.Queue): Queue for managing online tasks.
        _local_queue (queue.Queue): Queue for managing local tasks.
        _stop_event (threading.Event): Event to signal worker threads to stop.
        _lock (threading.Lock): Lock for synchronizing access to shared resources.
        _cached_raw_data (list): List to store fetched raw data.
        _abnormal_termination_info (str): Info about abnormal termination.
    """

    def __init__(
        self, fetch_data_callback, max_attempts=Config("MAX_ATTEMPT_TIMES")
    ):
        """
        Initialize the Factory instance.

        Args:
            fetch_data_callback (callable): Function to fetch data.
            max_attempts (int): Maximum retry attempts. Default is from Config.
        """
        self.fetch_data_callback = fetch_data_callback
        self.max_attempts = max_attempts
        self._online_queue = queue.Queue()
        self._local_queue = queue.Queue()
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self._cached_raw_data = []
        self._abnormal_termination_info = None

    def complete(self, task: Task):
        """
        Execute the task and process all timestamps.

        Args:
            task (Task): Task instance containing timestamps and worker counts.

        Returns:
            list: Cached raw data after processing.

        Raises:
            RuntimeError: If abnormal termination occurs during execution.
        """
        self._initialize_flow_line(task.timestamp_list)
        self._start_workers(task.online_worker_count, task.local_worker_count)
        self._online_queue.join()
        self._local_queue.join()
        self._stop_workers()
        if self._abnormal_termination_info:
            raise RuntimeError(self._abnormal_termination_info)
        return self._cached_raw_data

    def _initialize_flow_line(self, task_list):
        """
        Populate the online queue with initial tasks.

        Args:
            task_list (list): List of timestamps to process.
        """
        for ts in task_list:
            self._online_queue.put((ts, 0))  # Timestamp, retry count

    def _start_workers(self, online_worker_count, local_worker_count):
        """
        Start worker threads for online and local tasks.

        Args:
            online_worker_count (int): Number of online worker threads.
            local_worker_count (int): Number of local worker threads.
        """
        self.online_threads = self._start_threads(
            online_worker_count, self._online_worker
        )
        self.local_threads = self._start_threads(local_worker_count, self._local_worker)

    def _stop_workers(self):
        """
        Stop all worker threads and clear the queues.
        """
        self._stop_threads(self.local_threads, self._local_queue)
        self._stop_threads(self.online_threads, self._online_queue)

    def _start_threads(self, thread_count, target):
        """
        Start a specified number of threads.

        Args:
            thread_count (int): Number of threads to start.
            target (callable): Target function for each thread.

        Returns:
            list: List of started threading.Thread instances.
        """
        threads = []
        for _ in range(thread_count):
            t = threading.Thread(target=target)
            t.start()
            threads.append(t)
        return threads

    def _stop_threads(self, threads, queue):
        """
        Stop threads by adding None to the queue and joining threads.

        Args:
            threads (list): List of threading.Thread instances.
            queue (queue.Queue): Queue to signal thread termination.
        """
        for _ in range(len(threads)):
            queue.put(None)
        for t in threads:
            t.join()

    def _online_worker(self):
        """
        Worker thread for processing online tasks. Fetches data and handles retries.
        """
        while not self._stop_event.is_set():
            try:
                item = self._online_queue.get()
            except queue.Empty:
                continue
            if item is None:
                self._online_queue.task_done()
                break
            ts, attempt_times = item
            if attempt_times > self.max_attempts:
                with self._lock:
                    self._stop_event.set()
                    if self._abnormal_termination_info is None:
                        self._abnormal_termination_info = (
                            f"Exceeded max attempts ({attempt_times - 1}) for timestamp ({ts})."
                        )
            # TODO: Modify fetch logic with since=ts
            data, flag = self.fetch_data_callback(since=ts)
            self._local_queue.put((ts, data, flag, attempt_times + 1))
            self._online_queue.task_done()

    def _local_worker(self):
        """
        Worker thread for processing local tasks. Handles fetched data.
        """
        while not self._stop_event.is_set():
            try:
                item = self._local_queue.get()
            except queue.Empty:
                continue
            if item is None:
                self._local_queue.task_done()
                break
            ts, data, flag, attempt_times = item
            if flag == DataFlag.NORMAL:
                if data:
                    self._cached_raw_data.extend(data)
            else:
                self._online_queue.put((ts, attempt_times))
            self._local_queue.task_done()
