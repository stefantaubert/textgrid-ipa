from logging import Logger, getLogger
from typing import Generator, Iterable, List, Optional, Set

from textgrid.textgrid import Interval, IntervalTier, TextGrid

from textgrid_tools.globals import ExecutionResult
from textgrid_tools.helper import get_all_tiers, get_single_tier, interval_is_None_or_whitespace
from textgrid_tools.validation import (InvalidGridError, MultipleTiersWithThatNameError,
                                       NonDistinctTiersError, NotExistingTierError, ValidationError)


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


def map_tier(grid: TextGrid, tier_name: str, target_tier_names: Set[str], include_pauses: bool, logger: Optional[Logger]) -> ExecutionResult:
  """
  only_symbols: ignore intervals which marks contain only these symbols
  """
  # ignore_marks and only_symbols can be removed because it is in symbol_removing
  if logger is None:
    logger = getLogger(__name__)

  if error := InvalidGridError.validate(grid):
    return error, False

  if error := NotExistingTierError.validate(grid, tier_name):
    return error, False

  if error := MultipleTiersWithThatNameError.validate(grid, tier_name):
    return error, False

  for target_tier_name in target_tier_names:
    if error := NonDistinctTiersError.validate(tier_name, target_tier_name):
      return error, False

    if error := NotExistingTierError.validate(grid, target_tier_name):
      return error, False

  tier = get_single_tier(grid, tier_name)
  tier_intervals = list(get_intervals(tier, include_pauses))

  changed_anything = False

  for target_tier in get_all_tiers(grid, target_tier_names):
    target_tier_intervals = list(get_intervals(target_tier, include_pauses))

    if error := UnequalIntervalAmountError.validate(tier_intervals, target_tier_intervals):
      return error, False

    for tier_interval, target_tier_interval in zip(tier_intervals, target_tier_intervals):
      if target_tier_interval.mark != tier_interval.mark:
        target_tier_interval.mark = tier_interval.mark
        changed_anything = True

  return None, changed_anything


def get_intervals(tier: IntervalTier, include_pauses: bool) -> Generator[Interval, None, None]:
  tier_intervals = tier.intervals
  if not include_pauses:
    tier_intervals = ignore_pause_intervals(tier_intervals)
  return tier_intervals


def ignore_pause_intervals(intervals: Iterable[Interval]) -> Generator[Interval, None, None]:
  result = (
    interval
    for interval in intervals
    if not interval_is_None_or_whitespace(interval)
  )
  return result
