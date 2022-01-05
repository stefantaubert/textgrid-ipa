from typing import Iterable

from text_utils import StringFormat
from text_utils.types import Symbols
from textgrid.textgrid import Interval
from textgrid_tools.core.mfa.helper import interval_is_None_or_whitespace
from textgrid_tools.core.mfa.interval_format import IntervalFormat


def get_non_pause_symbols(intervals: Iterable[Interval], string_format: StringFormat) -> Iterable[Symbols]:
  for interval in intervals:
    if interval_is_None_or_whitespace(interval):
      continue
    symbols = string_format.convert_string_to_symbols(interval.mark)
    yield symbols


def merge_intervals(intervals: Iterable[Interval], intervals_string_format: StringFormat, intervals_format: IntervalFormat) -> Interval:
  assert len(intervals) > 0
  first_interval = intervals[0]
  last_interval = intervals[-1]

  non_pause_symbols = get_non_pause_symbols(intervals, intervals_string_format)
  joined_symbols = intervals_format.join_symbols(list(non_pause_symbols))
  mark = intervals_string_format.convert_symbols_to_string(joined_symbols)

  # is_pause = len(intervals) == 1 and interval_is_None_or_whitespace(intervals[0])
  # if is_pause:
  #   mark = intervals[0].mark
  # else:
  #   mark = intervals_to_text(
  #     intervals, tier_string_format.get_word_separator(), strip=False)
  interval = Interval(
    minTime=first_interval.minTime,
    maxTime=last_interval.maxTime,
    mark=mark,
  )
  return interval
