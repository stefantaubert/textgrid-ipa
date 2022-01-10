from logging import getLogger
from typing import Generator, Iterable, List, Set, cast

from text_utils import StringFormat
from textgrid.textgrid import Interval, TextGrid
from textgrid_tools.core.comparison import check_intervals_are_equal
from textgrid_tools.core.globals import ExecutionResult
from textgrid_tools.core.intervals.common import (merge_intervals,
                                                  replace_intervals)
from textgrid_tools.core.helper import (get_all_tiers,
                                        get_interval_readable,
                                        interval_is_None_or_whitespace)
from textgrid_tools.core.interval_format import IntervalFormat
from textgrid_tools.core.validation import (InvalidGridError,
                                            InvalidStringFormatIntervalError,
                                            NotExistingTierError,
                                            NotMatchingIntervalFormatError,
                                            ValidationError)


class DurationTooLowError(ValidationError):
  def __init__(self, duration: float) -> None:
    super().__init__()
    self.duration = duration

  @classmethod
  def validate(cls, duration: float):
    if not duration > 0:
      return cls(duration)
    return None

  @property
  def default_message(self) -> str:
    return f"Duration needs to be greater than zero but was \"{self.duration}\"!"


def join_intervals_on_durations(grid: TextGrid, tier_names: Set[str], tiers_string_format: StringFormat, tiers_interval_format: IntervalFormat, max_duration_s: float, include_empty_intervals: bool) -> ExecutionResult:
  assert len(tier_names) > 0

  if error := InvalidGridError.validate(grid):
    return error, False

  if error := DurationTooLowError.validate(max_duration_s):
    return error, False

  for tier_name in tier_names:
    if error := NotExistingTierError.validate(grid, tier_name):
      return error, False

  tiers = list(get_all_tiers(grid, tier_names))

  for tier in tiers:
    if error := InvalidStringFormatIntervalError.validate_tier(tier, tiers_string_format):
      return error, False

    if error := NotMatchingIntervalFormatError.validate_tier(tier, tiers_interval_format, tiers_string_format):
      return error, False

  changed_anything = False
  for tier in tiers:
    for interval in cast(Iterable[Interval], tier.intervals):
      if interval.duration() > max_duration_s:
        logger = getLogger(__name__)
        logger.warning(
          f"The duration of interval {get_interval_readable(interval)} ({interval.duration()}s) is bigger than {max_duration_s}!")

    for chunk in chunk_intervals(tier.intervals, max_duration_s, include_empty_intervals):
      merged_interval = merge_intervals(chunk, tiers_string_format, tiers_interval_format)
      if not check_intervals_are_equal(chunk, [merged_interval]):
        replace_intervals(tier, chunk, [merged_interval])
        changed_anything = True

  return None, changed_anything


def chunk_intervals(intervals: Iterable[Interval], max_duration_s: float, include_empty_intervals: bool) -> Generator[List[Interval], None, None]:
  current_intervals_duration = 0
  current_intervals = []
  for interval in intervals:
    if not include_empty_intervals and interval_is_None_or_whitespace(interval) and len(current_intervals) == 0:
      # do not include empty intervals as first interval in split-group
      yield [interval]
    if current_intervals_duration + interval.duration() <= max_duration_s:
      current_intervals.append(interval)
      current_intervals_duration += interval.duration()
    else:
      yield current_intervals
      current_intervals = [interval]
      current_intervals_duration = interval.duration()

  if len(current_intervals) > 0:
    yield current_intervals
    current_intervals = []
    current_intervals_duration = 0
