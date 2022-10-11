from logging import Logger, getLogger
from typing import Iterable, Optional, Set, cast

from textgrid.textgrid import Interval, TextGrid

from textgrid_tools.comparison import check_intervals_are_equal
from textgrid_tools.globals import ExecutionResult
from textgrid_tools.helper import get_all_tiers
from textgrid_tools.intervals.common import merge_intervals, replace_intervals
from textgrid_tools.validation import InvalidGridError, NotExistingTierError


def join_intervals(grid: TextGrid, tier_names: Set[str], join_with: str, ignore_empty: bool, logger: Optional[Logger]) -> ExecutionResult:
  assert len(tier_names) > 0

  if logger is None:
    logger = getLogger(__name__)

  if error := InvalidGridError.validate(grid):
    return error, False

  for tier_name in tier_names:
    if error := NotExistingTierError.validate(grid, tier_name):
      return error, False

  tiers = list(get_all_tiers(grid, tier_names))

  changed_anything = False
  for tier in tiers:
    intervals_copy = cast(Iterable[Interval], list(tier.intervals))
    merged_interval = merge_intervals(intervals_copy, join_with, ignore_empty)
    if not check_intervals_are_equal(intervals_copy, [merged_interval]):
      replace_intervals(tier, intervals_copy, [merged_interval])
      changed_anything = True

  return None, changed_anything
