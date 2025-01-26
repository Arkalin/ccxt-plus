import os

import numpy as np
import pandas as pd

from helpers.config import Config
from helpers.logger import Logger
from helpers.utils import Labels, timeframe_to_timestamp, timestamp_to_datetime
from helpers.errors import ExceedMaxMissingPointsError


def _id(func_id):
    """Decorator to assign an ID to a method for mapping purposes."""

    def decorator(func):
        func.id = func_id
        return func

    return decorator


class CSVSaver:
    """
    A class to handle saving processed data into CSV files with additional data integrity
    and handling of missing time points.

    Attributes:
        labels (Labels): Labels used to construct the working folder path.
        actions (list): List of actions to apply on the data.
        columns (list): List of column names in the data.
        time_column_index (int): Index of the column containing timestamps.
        timeframe (str): Timeframe interval for missing time calculation.
    """

    def __init__(
        self,
        labels: Labels,
        actions: list,
        columns: list,
        time_column_index: int,
        timeframe: str = None,
    ):
        """
        Initialize the CSVSaver instance.

        Args:
            labels (Labels): Labels used to construct the working folder path.
            actions (list): List of actions to apply on the data.
            columns (list): List of column names in the data.
            time_column_index (int): Index of the column containing timestamps.
            timeframe (str, optional): Timeframe interval for missing time calculation.
        """
        self.labels = labels
        self.actions = actions
        self.columns = columns
        self.timeframe = timeframe
        self._time_column_name = columns[time_column_index]
        self._work_folder = self._initialize_work_folder()
        self._df: pd.DataFrame = None
        self._missing_times: set = None
        self._actions = {}
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if callable(attr) and hasattr(attr, "id"):
                self._actions[attr.id] = attr

    def _initialize_work_folder(self):
        """
        Create and initialize the working folder for saving CSV files.

        Returns:
            str: Path to the working folder.
        """
        work_folder = os.path.join(Config("DATA_PATH"), *self.labels)
        os.makedirs(work_folder, exist_ok=True)
        return work_folder

    @_id("sort")
    def _sort(self, ascending=True):
        """
        Sort the data by the time column.

        Args:
            ascending (bool, optional): Whether to sort in ascending order. Defaults to True.
        """
        self._df.sort_values(
            by=self._time_column_name, ascending=ascending, inplace=True
        )

    @_id("drop_duplicates")
    def _drop_duplicates(self):
        """
        Drop duplicate rows based on the time column, keeping the first occurrence.
        """
        self._df.drop_duplicates(
            subset=[self._time_column_name], keep="first", inplace=True
        )

    @_id("drop_last")
    def _drop_last(self):
        """
        Drop the last row in the DataFrame.
        """
        self._df = self._df.iloc[:-1]

    @_id("transfer_time")
    def _transfer_time(self):
        """
        Convert the time column from milliseconds to a pandas datetime format.
        """
        # self._df[self._time_column_name] = pd.to_datetime(
        #     self._df[self._time_column_name], unit="ms"
        # )
        self._df[self._time_column_name] = self._df[self._time_column_name].apply(timestamp_to_datetime)

    def _initialize_missing_times(self):
        """
        Identify missing time points in the data based on the given timeframe.

        Returns:
            bool: True if missing times are initialized, False if no data exists.

        Raises:
            ValueError: If timeframe is not provided.
            RuntimeError: If the number of missing time points exceeds the allowed maximum.
        """
        if self._missing_times is not None:
            return True
        if self.timeframe is None:
            raise ValueError("Missing timeframe, cannot retrieve missing times")
        df = self._df
        if df.empty:
            Logger.warning("No data available, no missing points exist")
            return False

        df[self._time_column_name] = df[self._time_column_name].astype(np.int64)

        min_time = df[self._time_column_name].min()
        max_time = df[self._time_column_name].max()

        delta_timestamp = timeframe_to_timestamp(self.timeframe)
        expected_timestamps = np.arange(
            min_time, max_time + delta_timestamp, delta_timestamp
        )
        existing_timestamps = set(df[self._time_column_name].values)
        missing_timestamps = set(expected_timestamps) - existing_timestamps

        if not missing_timestamps:
            Logger.info("All expected time points are present")
            self._missing_times = set()
            return True
        if len(missing_timestamps) > Config("ALLOW_MAX_MISSING_TIMESTAMPS"):
            raise ExceedMaxMissingPointsError(
                f"Too many missing time points: {len(missing_timestamps)}"
            )
        Logger.info(f"Total {len(missing_timestamps)} missing data points")
        self._missing_times = sorted(missing_timestamps)
        return True

    @_id("fix_integrity")
    def _fix_data_integrity(self):
        """
        Fill missing data points using neighboring data points.

        Requirements:
            The DataFrame must be sorted by the time column.
        """
        if not self._initialize_missing_times():
            return
        if len(self._missing_times) == 0:
            return
        df = self._df
        new_data = []
        arr = df[self._time_column_name].values
        for missing_ts in self._missing_times:
            insert_pos = np.searchsorted(arr, missing_ts)
            candidates = []
            if insert_pos > 0:
                candidates.append(
                    (abs(arr[insert_pos - 1] - missing_ts), insert_pos - 1)
                )
            if insert_pos < len(arr):
                candidates.append((abs(arr[insert_pos] - missing_ts), insert_pos))

            closest_idx = min(candidates, key=lambda x: x[0])[1]
            closest_data = df.iloc[closest_idx].copy()
            closest_data[self._time_column_name] = missing_ts
            new_data.append(closest_data)

        if new_data:
            self._append_data([row for row in new_data])
            self._sort()

    def _append_data(self, data_list):
        """
        Append new data rows to the existing DataFrame.

        Args:
            data_list (list): List of rows to append.
        """
        try:
            new_df = pd.DataFrame(data_list, columns=self.columns)
            if self._df is None:
                self._df = new_df
            else:
                self._df = pd.concat([self._df, new_df], ignore_index=True)
        except Exception as e:
            Logger.error(f"An error occurs when appending data: {e}")

    @_id("save_missing_times")
    def _save_missing_times(self):
        """
        Save missing time points to a text file in the working folder.
        """
        if not self._initialize_missing_times():
            return
        if len(self._missing_times) == 0:
            return
        file_name = os.path.join(self._work_folder, "missingtimes.txt")
        with open(file_name, "w") as f:
            for missing_timestamp in self._missing_times:
                missing_time = timestamp_to_datetime(missing_timestamp)
                f.write(f"{missing_time} ({missing_timestamp})\n")
        Logger.info(f"Missing times saved in {file_name}")

    def save(self, processed_data):
        """
        Save processed data to CSV files after applying the specified actions.

        Args:
            processed_data (list): List of rows to process and save.
        """
        self._append_data(processed_data)
        for action in self.actions:
            func = self._actions.get(action)
            if func:
                func()
            else:
                Logger.warning(f"Cannot find action: {action}")
        self._save_file()

    def _save_file(self):
        """
        Save the data to CSV files in chunks, based on the configured chunk size.
        """
        df = self._df
        chunk_size = Config("CSV_CHUNK_SIZE")
        file_count = 0
        for i in range(0, len(df), chunk_size):
            chunk = df.iloc[i : i + chunk_size]
            output_file = os.path.join(self._work_folder, f"{file_count}.csv")
            chunk.to_csv(output_file, index=False, header=self.columns)
            file_count += 1
        Logger.info(
            f"Created {file_count} file{'s' if file_count > 1 else ''} in {self._work_folder}"
        )
