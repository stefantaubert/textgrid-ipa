from typing import List

from textgrid import Interval

from textgrid_tools.comparison import check_interval_is_equal, check_intervals_are_equal


def assert_interval_is_equal(interval1: Interval, interval2: Interval):
  assert check_interval_is_equal(interval1, interval2)


def assert_intervals_are_equal(intervals1: List[Interval], intervals2: List[Interval]) -> None:
  assert check_intervals_are_equal(intervals1, intervals2)
