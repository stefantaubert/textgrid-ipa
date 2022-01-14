from typing import Generator, Iterable, List, Set

from text_utils.string_format import StringFormat
from text_utils.types import Symbol
from text_utils.utils import symbols_ignore
from textgrid.textgrid import Interval, IntervalTier, TextGrid
from textgrid_tools.core.globals import ExecutionResult
from textgrid_tools.core.helper import (get_all_tiers, get_mark,
                                        get_mark_symbols, get_single_tier,
                                        interval_is_None_or_whitespace)
from textgrid_tools.core.validation import (InvalidGridError,
                                            InvalidStringFormatIntervalError,
                                            MultipleTiersWithThatNameError,
                                            NonDistinctTiersError,
                                            NotExistingTierError,
                                            ValidationError)


class UnequalIntervalAmountError(ValidationError):
  def __init__(self, tier_intervals: List[Interval], target_tier_intervals: List[Interval]) -> None:
    super().__init__()
    self.tier_intervals = tier_intervals
    self.target_tier_intervals = target_tier_intervals

  @classmethod
  def validate(cls, tier_intervals: List[Interval], target_tier_intervals: List[Interval]):
    if len(tier_intervals) != len(target_tier_intervals):
      return cls(tier_intervals, target_tier_intervals)
    return None

  @property
  def default_message(self) -> str:
    msg = f"Amount of intervals is different: {len(self.tier_intervals)} vs. {len(self.target_tier_intervals)} (target)!\n\n"
    display_first_n_max = 250
    min_len = min(len(self.target_tier_intervals), len(self.tier_intervals), display_first_n_max)
    for i in range(min_len):
      msg += f"===> \"{self.tier_intervals[i].mark}\" vs. \"{self.target_tier_intervals[i].mark}\"\n"
    msg += "..."
    return msg


def map_tier(grid: TextGrid, tier_name: str, tier_string_format: StringFormat, target_tier_names: Set[str], targets_string_format: StringFormat, include_pauses: bool, ignore_marks: Set[str], only_symbols: Set[Symbol]) -> ExecutionResult:
  """
  only_symbols: ignore intervals which marks contain only these symbols
  """

  if error := InvalidGridError.validate(grid):
    return error, False

  if error := NotExistingTierError.validate(grid, tier_name):
    return error, False

  if error := MultipleTiersWithThatNameError.validate(grid, tier_name):
    return error, False

  tier = get_single_tier(grid, tier_name)

  if error := InvalidStringFormatIntervalError.validate_tier(tier, tier_string_format):
    return error, False

  for target_tier_name in target_tier_names:
    if error := NonDistinctTiersError.validate(tier_name, target_tier_name):
      return error, False

    if error := NotExistingTierError.validate(grid, target_tier_name):
      return error, False

  tier_intervals = list(get_intervals(tier, include_pauses,
                        ignore_marks, only_symbols, tier_string_format))

  changed_anything = False

  for target_tier in get_all_tiers(grid, target_tier_names):
    if error := InvalidStringFormatIntervalError.validate_tier(target_tier, targets_string_format):
      return error, False

    target_tier_intervals = list(get_intervals(
      target_tier, include_pauses, ignore_marks, only_symbols, targets_string_format))

    if error := UnequalIntervalAmountError.validate(tier_intervals, target_tier_intervals):
      return error, False

    for tier_interval, target_tier_interval in zip(tier_intervals, target_tier_intervals):
      if target_tier_interval.mark != tier_interval.mark:
        target_tier_interval.mark = tier_interval.mark
        changed_anything = True

  return None, changed_anything


def get_intervals(tier: IntervalTier, include_pauses: bool, ignore_marks: Set[str], only_symbols: Set[str], string_format: StringFormat) -> Generator[Interval, None, None]:
  tier_intervals = tier.intervals
  if not include_pauses:
    tier_intervals = remove_empty_intervals(tier_intervals)
  if len(ignore_marks) > 0:
    tier_intervals = remove_intervals_with_marks(tier_intervals, ignore_marks)
  if len(only_symbols) > 0:
    tier_intervals = remove_intervals_with_only_symbols(tier_intervals, only_symbols, string_format)
  return tier_intervals


def remove_empty_intervals(intervals: Iterable[Interval]) -> Generator[Interval, None, None]:
  result = (
    interval
    for interval in intervals
    if not interval_is_None_or_whitespace(interval)
  )
  return result


def remove_intervals_with_marks(intervals: Iterable[Interval], ignore_marks: Set[str]) -> Generator[Interval, None, None]:
  result = (
    interval
    for interval in intervals
    if get_mark(interval) not in ignore_marks
  )
  return result


def remove_intervals_with_only_symbols(intervals: Iterable[Interval], only_symbols: Set[str], string_format: StringFormat) -> Generator[Interval, None, None]:
  result = (
    interval
    for interval in intervals
    if len(symbols_ignore(get_mark_symbols(interval, string_format), only_symbols)) > 0
  )
  return result
