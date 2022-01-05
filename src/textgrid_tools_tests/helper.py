from typing import Collection

from textgrid import Interval
from textgrid_tools.core.comparison import (check_interval_is_equal,
                                            check_intervals_are_equal)


def assert_interval_is_equal(interval1: Interval, interval2: Interval):
  assert check_interval_is_equal(interval1, interval2)


def assert_intervals_are_equal(intervals1: Collection[Interval], intervals2: Collection[Interval]) -> None:
  assert check_intervals_are_equal(intervals1, intervals2)
