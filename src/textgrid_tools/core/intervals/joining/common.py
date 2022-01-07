from typing import Collection, List, Optional, Set

from text_utils import StringFormat
from text_utils.types import Symbol
from textgrid.textgrid import Interval, IntervalTier
from textgrid_tools.core.mfa.helper import get_mark_symbols_intervals
from textgrid_tools.core.mfa.interval_format import (IntervalFormat,
                                                     merge_interval_symbols)


def merge_intervals(intervals: Collection[Interval], intervals_string_format: StringFormat, intervals_interval_format: IntervalFormat, join_symbols: Optional[Set[Symbol]] = None, ignore_join_symbols: Optional[Set[Symbol]] = None) -> Interval:
  assert len(intervals) > 0
  interval_symbols = list(get_mark_symbols_intervals(intervals, intervals_string_format))
  joined_interval_symbols = list(merge_interval_symbols(
    interval_symbols, intervals_interval_format, join_symbols, ignore_join_symbols))
  assert len(interval_symbols) < len(joined_interval_symbols)

  if len(joined_interval_symbols) == 1:
    mark = intervals_string_format.convert_symbols_to_string(joined_interval_symbols[0])

    first_interval = intervals[0]
    last_interval = intervals[-1]

    interval = Interval(
      minTime=first_interval.minTime,
      maxTime=last_interval.maxTime,
      mark=mark,
    )
    return interval

  raise NotImplementedError()


def replace_intervals(tier: IntervalTier, intervals: List[Interval], replace_with: List[Interval]) -> None:
  assert len(intervals) > 0
  assert len(replace_with) > 0
  assert intervals[0].minTime == replace_with[0].minTime
  assert intervals[-1].maxTime == replace_with[-1].maxTime
  from_index = tier.intervals.index(intervals[0])
  for interval in intervals:
    tier.intervals.remove(interval)

  for interval in reversed(replace_with):
    tier.intervals.insert(from_index, interval)
