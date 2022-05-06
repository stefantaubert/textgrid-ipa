from collections import OrderedDict
from logging import Logger, getLogger
from math import inf
from typing import Iterable, List, Optional, Tuple, cast

from textgrid import Interval, IntervalTier, TextGrid

from textgrid_tools.globals import ExecutionResult
from textgrid_tools.helper import check_intervals_are_consecutive
from textgrid_tools.intervals.boundary_fixing import fix_interval_boundaries
from textgrid_tools.validation import InvalidGridError, ValidationError


class TiersNotSameError(ValidationError):
  def __init__(self, grid1: TextGrid, grid2: TextGrid) -> None:
    super().__init__()
    self.grid1 = grid1
    self.tier_nagrid2me = grid2

  @classmethod
  def validate(cls, grid1: TextGrid, grid2: TextGrid):
    if not get_tier_names(grid1) == get_tier_names(grid2):
      return cls(grid1, grid2)
    return None


def get_tier_names(grid: TextGrid):
  tier_names = {tier.name for tier in grid.tiers}
  return tier_names


def merge_grids(grids: List[TextGrid], insert_duration: Optional[float], insert_mark: Optional[str], logger: Optional[Logger]) -> Tuple[ExecutionResult, Optional[TextGrid]]:
  assert len(grids) > 0

  if logger is None:
    logger = getLogger(__name__)

  if len(grids) == 1:
    return (None, False), grids[0]

  ref_grid = grids[0]

  for grid in grids:
    if error := InvalidGridError.validate(grid):
      return (error, False), None

    if error := TiersNotSameError.validate(grid, ref_grid):
      return (error, False), None

  target_tiers = OrderedDict((
    (tier.name, tier.intervals)
    for tier in cast(List[IntervalTier], ref_grid.tiers)
  ))

  for grid in grids[1:]:
    for tier in cast(List[IntervalTier], ref_grid.tiers):
      if insert_duration is not None:
        assert insert_duration > 0
        insert_interval = Interval(0.0, insert_duration, insert_mark)
        target_tiers[tier.name].append(insert_interval)
      target_tiers[tier.name].extend(tier.intervals)

  result = TextGrid()

  min_time = 0
  for tier, intervals in target_tiers.items():
    max_time = set_times_consecutive_from_durations(intervals, min_time)
    grid_tier = IntervalTier(tier, min_time, max_time)
    grid_tier.intervals = intervals
    result.append(grid_tier)

  result.minTime = min_time
  result.maxTime = result.tiers[0].maxTime

  if len(target_tiers) > 1:
    tier_names = list(target_tiers.keys())
    fix_interval_boundaries(result, grid.tiers[0].name, tier_names[1:], inf, logger)
  return (None, True), result


def set_times_consecutive_from_durations(intervals: Iterable[Interval], init_min_time: float) -> float:
  last_time = init_min_time
  for interval in intervals:
    duration = interval.duration()
    new_max_time = last_time + duration
    interval.minTime = last_time
    interval.maxTime = new_max_time
    last_time = new_max_time
  assert check_intervals_are_consecutive(intervals)
  return last_time
