from typing import Generator, Iterable, Optional, Set, cast

from text_utils import StringFormat, Symbol
from textgrid.textgrid import Interval, TextGrid
from textgrid_tools.comparison import check_intervals_are_equal
from textgrid_tools.globals import ExecutionResult
from textgrid_tools.helper import (get_all_tiers,
                                   interval_is_None_or_whitespace)
from textgrid_tools.interval_format import (IntervalFormat,
                                            has_lower_format,
                                            split_interval_symbols)
from textgrid_tools.intervals.common import replace_intervals
from textgrid_tools.validation import (InvalidGridError,
                                       InvalidStringFormatIntervalError,
                                       NotExistingTierError,
                                       NotMatchingIntervalFormatError,
                                       ValidationError)


class InvalidIntervalFormatError(ValidationError):
  def __init__(self, tier_interval_format: IntervalFormat) -> None:
    super().__init__()
    self.tier_interval_format = tier_interval_format

  @classmethod
  def validate(cls, tier_interval_format: IntervalFormat):
    if not has_lower_format(tier_interval_format):
      return cls(tier_interval_format)
    return None

  @property
  def default_message(self) -> str:
    return f"{str(self.tier_interval_format)} marks could not be further split."


def split(grid: TextGrid, tier_names: Set[str], tiers_string_format: StringFormat, tiers_interval_format: IntervalFormat, join_symbols: Optional[Set[Symbol]], ignore_join_symbols: Optional[Set[Symbol]]) -> ExecutionResult:
  assert len(tier_names) > 0

  if error := InvalidGridError.validate(grid):
    return error, False

  if error := InvalidIntervalFormatError.validate(tiers_interval_format):
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
    intervals_copy = cast(Iterable[Interval], list(tier.intervals))
    for interval in intervals_copy:
      splitted_intervals = list(get_split_intervals(
        interval, tiers_string_format, tiers_interval_format, join_symbols, ignore_join_symbols))

      if not check_intervals_are_equal([interval], splitted_intervals):
        replace_intervals(tier, [interval], splitted_intervals)
        changed_anything = True

  return None, changed_anything


def get_split_intervals(interval: Interval, tier_string_format: StringFormat, tier_interval_format: IntervalFormat, join_symbols: Optional[Set[Symbol]], ignore_join_symbols: Optional[Set[Symbol]]) -> Generator[Interval, None, None]:
  if interval_is_None_or_whitespace(interval):
    yield interval

  mark_symbols = tier_string_format.convert_string_to_symbols(interval.mark)
  split_mark_symbols = list(split_interval_symbols(
    mark_symbols, tier_interval_format, join_symbols, ignore_join_symbols))
  count_of_symbols = sum(len(new_mark_symbols) for new_mark_symbols in split_mark_symbols)
  current_timepoint = interval.minTime
  interval_duration = interval.duration()
  # print("split_mark_symbols", len(split_mark_symbols))
  for i, symbols in enumerate(split_mark_symbols):
    assert len(symbols) > 0

    duration = interval_duration * (len(symbols) / count_of_symbols)
    string = tier_string_format.convert_symbols_to_string(symbols)

    min_time = current_timepoint
    is_last = i == len(split_mark_symbols) - 1
    if is_last:
      max_time = interval.maxTime
    else:
      max_time = current_timepoint + duration

    # if not min_time < max_time:
    #   print(split_mark_symbols)
    #   print(count_of_symbols)
    assert min_time < max_time

    new_interval = Interval(
      minTime=min_time,
      maxTime=max_time,
      mark=string,
    )

    current_timepoint = max_time
    yield new_interval
