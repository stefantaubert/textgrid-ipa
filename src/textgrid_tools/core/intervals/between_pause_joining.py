from typing import Generator, Iterable, List, Optional, Set, cast

from text_utils import StringFormat, Symbol
from textgrid.textgrid import Interval, TextGrid
from textgrid_tools.core.comparison import check_intervals_are_equal
from textgrid_tools.core.globals import ExecutionResult
from textgrid_tools.core.helper import get_all_tiers, get_intervals_duration
from textgrid_tools.core.interval_format import IntervalFormat
from textgrid_tools.core.intervals.common import (
    group_adjacent_pauses, merge_intervals, merge_intervals_custom_symbol,
    replace_intervals)
from textgrid_tools.core.validation import (InvalidGridError,
                                            InvalidStringFormatIntervalError,
                                            NotExistingTierError,
                                            NotMatchingIntervalFormatError,
                                            ValidationError)


class PauseTooLowError(ValidationError):
  def __init__(self, pause: float) -> None:
    super().__init__()
    self.pause = pause

  @classmethod
  def validate(cls, pause: float):
    if not pause >= 0:
      return cls(pause)
    return None

  @property
  def default_message(self) -> str:
    return f"Pause needs to be greater than or equal to zero but was \"{self.pause}\"!"


def join_intervals_between_pauses(grid: TextGrid, tier_names: Set[str], tiers_string_format: StringFormat, tiers_interval_format: IntervalFormat, pause: float, custom_join_symbol: Optional[Symbol]) -> ExecutionResult:
  assert len(tier_names) > 0

  if error := InvalidGridError.validate(grid):
    return error, False

  if error := PauseTooLowError.validate(pause):
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
    for chunk in chunk_intervals(intervals_copy, pause):
      if custom_join_symbol is None:
        merged_interval = merge_intervals(chunk, tiers_string_format, tiers_interval_format)
      else:
        merged_interval = merge_intervals_custom_symbol(
          chunk, tiers_string_format, custom_join_symbol)
      if not check_intervals_are_equal(chunk, [merged_interval]):
        replace_intervals(tier, chunk, [merged_interval])
        changed_anything = True

  return None, changed_anything


def chunk_intervals(intervals: Iterable[Interval], pause: float) -> Generator[List[Interval], None, None]:
  chunk = []
  intervals_with_grouped_pauses = group_adjacent_pauses(intervals)
  for interval_or_pause_group in intervals_with_grouped_pauses:
    is_pause = isinstance(interval_or_pause_group, list)
    if is_pause:
      if get_intervals_duration(interval_or_pause_group) <= pause:
        # extend because they should be merged
        chunk.extend(interval_or_pause_group)
      else:
        if len(chunk) > 0:
          yield chunk
          chunk = []
        for pause_interval in interval_or_pause_group:
          # yield each because they should not be merged
          yield [pause_interval]
    else:
      assert isinstance(interval_or_pause_group, Interval)
      chunk.append(interval_or_pause_group)

  if len(chunk) > 0:
    yield chunk
