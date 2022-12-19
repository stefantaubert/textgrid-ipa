from logging import Logger, getLogger
from typing import Generator, Iterable, List, Literal, Optional, Set

from ordered_set import OrderedSet
from textgrid.textgrid import Interval, TextGrid

from textgrid_tools.globals import ExecutionResult
from textgrid_tools.helper import get_all_tiers, get_single_tier
from textgrid_tools.validation import (InvalidGridError, MultipleTiersWithThatNameError,
                                       NonDistinctTiersError, NotExistingTierError, ValidationError)

# DISPLAY_FIRST_N_MAX = 5000


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
    min_len = min(len(self.target_tier_intervals), len(self.tier_intervals))
    for i in range(min_len):
      msg += f"===> \"{self.tier_intervals[i].mark}\" vs. \"{self.target_tier_intervals[i].mark}\" ({self.tier_intervals[i].minTime}; {self.target_tier_intervals[i].minTime})\n"
    msg += "..."
    return msg


def map_tier(grid: TextGrid, tier_name: str, target_tier_names: Set[str], filter_from: OrderedSet[str], filter_to: OrderedSet[str], filter_from_mode: Literal["consider", "ignore"], filter_to_mode: Literal["consider", "ignore"], mode: Literal["replace", "prepend", "append"], logger: Optional[Logger]) -> ExecutionResult:
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
  tier_intervals = list(filter_intervals(tier, filter_from, filter_from_mode))

  changed_anything = False

  for target_tier in get_all_tiers(grid, target_tier_names):
    target_tier_intervals = list(filter_intervals(target_tier, filter_to, filter_to_mode))

    if error := UnequalIntervalAmountError.validate(tier_intervals, target_tier_intervals):
      return error, False

    for tier_interval, target_tier_interval in zip(tier_intervals, target_tier_intervals):
      if mode == "replace":
        if target_tier_interval.mark != tier_interval.mark:
          target_tier_interval.mark = tier_interval.mark
          changed_anything = True
      elif mode == "prepend":
        target_tier_interval.mark = f"{tier_interval.mark}{target_tier_interval.mark}"
        changed_anything = True
      elif mode == "append":
        target_tier_interval.mark = f"{target_tier_interval.mark}{tier_interval.mark}"
        changed_anything = True
      else:
        assert False

  return None, changed_anything


def filter_intervals(intervals: Iterable[Interval], filter_set: OrderedSet[str], mode: Literal["consider", "ignore"]) -> Generator[Interval, None, None]:
  if mode == "consider":
    return consider_intervals(intervals, filter_set)
  if mode == "ignore":
    return ignore_intervals(intervals, filter_set)
  assert False
  raise NotImplementedError()


def ignore_intervals(intervals: Iterable[Interval], ignore: OrderedSet[str]) -> Generator[Interval, None, None]:
  result = (
    interval
    for interval in intervals
    if interval.mark not in ignore
  )
  yield from result


def consider_intervals(intervals: Iterable[Interval], consider: OrderedSet[str]) -> Generator[Interval, None, None]:
  result = (
    interval
    for interval in intervals
    if interval.mark in consider
  )
  yield from result
