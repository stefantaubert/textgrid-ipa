from typing import Collection, Iterable

from textgrid import Interval


def assert_interval_is_equal(interval1: Interval, interval2: Interval):
  result = interval1 == interval2
  result &= interval1.mark == interval2.mark
  assert result


def assert_intervals_are_equal(intervals1: Collection[Interval], intervals2: Collection[Interval]) -> None:
  if len(intervals1) != len(intervals2):
    assert False
  for interval1, interval2 in zip(intervals1, intervals2):
    assert_interval_is_equal(interval1, interval2)
