from logging import Logger, getLogger
from typing import Optional

from textgrid import Interval, IntervalTier, TextGrid

from textgrid_tools.globals import ExecutionResult
from textgrid_tools.helper import check_is_valid_grid, set_intervals_consecutive
from textgrid_tools.validation import ExistingTierError, InvalidGridError


def import_text_to_tier(grid: TextGrid, tier_name: str, text: str, sep: str, logger: Optional[Logger]) -> ExecutionResult:
  if logger is None:
    logger = getLogger(__name__)

  if error := InvalidGridError.validate(grid):
    return error, False

  if error := ExistingTierError.validate(grid, tier_name):
    return error, False

  new_tier = IntervalTier(tier_name, grid.minTime, grid.maxTime)
  interval_marks = text.split(sep)
  intervals = [Interval(0, 1, mark) for mark in interval_marks]
  set_intervals_consecutive(intervals, grid.minTime, grid.maxTime)
  new_tier.intervals.extend(intervals)
  grid.append(new_tier)

  assert check_is_valid_grid(grid)

  return None, True
