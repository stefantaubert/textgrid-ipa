from typing import List

from textgrid import Interval
from textgrid.textgrid import IntervalTier


def check_tiers_are_equal(tier1: IntervalTier, tier2: IntervalTier) -> bool:
  if tier1.name != tier2.name:
    return False
  if tier1.minTime != tier2.minTime:
    return False
  if tier1.maxTime != tier2.maxTime:
    return False
  return check_intervals_are_equal(tier1.intervals, tier2.intervals)


def check_intervals_are_equal(intervals1: List[Interval], intervals2: List[Interval]) -> bool:
  if len(intervals1) != len(intervals2):
    return False

  for interval1, interval2 in zip(intervals1, intervals2):
    if not check_interval_is_equal(interval1, interval2):
      return False

  return True


def check_interval_is_equal(interval1: Interval, interval2: Interval) -> bool:
  # Note: __eq__ is not a good implemented
  # result = interval1 == interval2

  if interval1.mark != interval2.mark:
    return False

  if interval1.minTime != interval2.minTime:
    return False

  if interval1.maxTime != interval2.maxTime:
    return False

  if interval1.strict != interval2.strict:
    return False

  return True
