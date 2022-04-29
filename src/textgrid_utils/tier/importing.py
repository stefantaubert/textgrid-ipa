from textgrid import Interval, IntervalTier
from textgrid.textgrid import TextGrid

from textgrid_utils.globals import ExecutionResult
from textgrid_utils.helper import check_is_valid_grid, set_intervals_consecutive
from textgrid_utils.validation import ExistingTierError, InvalidGridError


def import_text_to_tier(grid: TextGrid, tier_name: str, text: str, sep: str) -> ExecutionResult:
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
