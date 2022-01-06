from typing import Generator, Optional, Set

from pronunciation_dict_parser.parser import Symbol
from text_utils import StringFormat
from textgrid.textgrid import Interval, IntervalTier, TextGrid
from textgrid_tools.core.globals import ExecutionResult
from textgrid_tools.core.mfa.helper import (add_or_update_tier, get_first_tier,
                                            interval_is_None_or_whitespace)
from textgrid_tools.core.mfa.interval_format import (IntervalFormat,
                                                     has_lower_format,
                                                     split_interval_symbols)
from textgrid_tools.core.validation import (ExistingTierError,
                                            InvalidGridError,
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


def split_intervals(grid: TextGrid, tier_name: str, tier_string_format: StringFormat, tier_interval_format: IntervalFormat, join_symbols: Optional[Set[Symbol]], ignore_join_symbols: Optional[Set[Symbol]], custom_output_tier_name: Optional[str] = None, overwrite_tier: bool = True) -> ExecutionResult:
  if error := InvalidGridError.validate(grid):
    return error, False

  if error := NotExistingTierError.validate(grid, tier_name):
    return error, False

  if error := InvalidIntervalFormatError.validate(tier_interval_format):
    return error, False

  output_tier_name = tier_name
  if custom_output_tier_name is not None:
    if not overwrite_tier and (error := ExistingTierError.validate(grid, custom_output_tier_name)):
      return error, False
    output_tier_name = custom_output_tier_name

  tier = get_first_tier(grid, tier_name)

  if error := NotMatchingIntervalFormatError.validate(tier, tier_interval_format, tier_string_format):
    return error, False

  target_intervals = (
    new_interval
    for interval in tier.intervals
    for new_interval in get_split_intervals(interval, tier_string_format, tier_interval_format, join_symbols, ignore_join_symbols)
  )

  output_tier = IntervalTier(
    name=output_tier_name,
    minTime=tier.minTime,
    maxTime=tier.maxTime,
  )

  output_tier.intervals.extend(target_intervals)

  changed_anything = add_or_update_tier(grid, tier, output_tier, overwrite_tier)

  return None, changed_anything


def get_split_intervals(interval: Interval, tier_string_format: StringFormat, tier_interval_format: IntervalFormat, join_symbols: Optional[Set[Symbol]], ignore_join_symbols: Optional[Set[Symbol]]) -> Generator[Interval, None, None]:
  if interval_is_None_or_whitespace(interval):
    yield interval

  mark_symbols = tier_string_format.convert_string_to_symbols(interval.mark)
  split_mark_symbols = list(split_interval_symbols(
    mark_symbols, tier_interval_format, join_symbols, ignore_join_symbols))

  count_of_symbols = sum(1 for new_mark_symbols in split_mark_symbols for _ in new_mark_symbols)
  current_timepoint = interval.minTime
  print("split_mark_symbols", len(split_mark_symbols))
  for i, split_mark_symbols in enumerate(split_mark_symbols):
    string = tier_string_format.convert_symbols_to_string(split_mark_symbols)
    duration = interval.duration() * (len(split_mark_symbols) / count_of_symbols)
    print(interval.duration(), len(split_mark_symbols), count_of_symbols)
    min_time = current_timepoint

    is_last = i == len(split_mark_symbols) - 1
    if is_last:
      max_time = interval.maxTime
    else:
      max_time = current_timepoint + duration

    new_interval = Interval(
      minTime=min_time,
      maxTime=max_time,
      mark=string,
    )

    current_timepoint = max_time
    yield new_interval
