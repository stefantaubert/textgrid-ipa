from typing import (Collection, Generator, Iterable, List, Optional, Set,
                    Tuple, Union)

from text_utils import StringFormat
from text_utils.types import Symbol
from textgrid.textgrid import Interval, IntervalTier
from textgrid_tools.core.helper import (get_mark_symbols_intervals,
                                        interval_is_None_or_whitespace)
from textgrid_tools.core.interval_format import (IntervalFormat,
                                                 merge_interval_symbols)


def merge_intervals(intervals: Collection[Interval], intervals_string_format: StringFormat, intervals_interval_format: IntervalFormat, join_symbols: Optional[Set[Symbol]] = None, ignore_join_symbols: Optional[Set[Symbol]] = None) -> Interval:
  assert len(intervals) > 0
  interval_symbols = list(get_mark_symbols_intervals(intervals, intervals_string_format))
  joined_interval_symbols = list(merge_interval_symbols(
    interval_symbols, intervals_interval_format, join_symbols, ignore_join_symbols))
  assert 0 <= len(joined_interval_symbols) <= len(interval_symbols)

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


def group_adjacent_pauses(intervals: Iterable[Interval]) -> Generator[Union[Interval, List[Interval]], None, None]:
  pause_group = []
  for interval in intervals:
    is_pause = interval_is_None_or_whitespace(interval)
    if is_pause:
      pause_group.append(interval)
    else:
      if len(pause_group) > 0:
        yield pause_group
        pause_group = []
      yield interval

  if len(pause_group) > 0:
    yield pause_group


def group_adjacent_pauses2(intervals: Iterable[Interval]) -> Generator[Tuple[List[Interval], bool], None, None]:
  pause_group = []
  for interval in intervals:
    is_pause = interval_is_None_or_whitespace(interval)
    if is_pause:
      pause_group.append(interval)
    else:
      if len(pause_group) > 0:
        yield pause_group, True
        pause_group = []
      yield [interval], False

  if len(pause_group) > 0:
    yield pause_group, True


def group_adjacent_content_and_pauses(intervals: Iterable[Interval]) -> Generator[Tuple[List[Interval], bool], None, None]:
  current_group = []
  current_group_is_pause: Optional[bool] = None
  for interval in intervals:
    is_pause = interval_is_None_or_whitespace(interval)
    same_group = current_group_is_pause is not None and current_group_is_pause == is_pause
    if not same_group and len(current_group) > 0:
      assert current_group_is_pause is not None
      yield current_group, current_group_is_pause
      current_group = []
    current_group.append(interval)
    current_group_is_pause = is_pause

  if len(current_group) > 0:
    assert current_group_is_pause is not None
    yield current_group, current_group_is_pause
