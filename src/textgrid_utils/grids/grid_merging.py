from collections import OrderedDict
from math import inf
from typing import Iterable, List, Optional, Tuple, cast

from textgrid import Interval, IntervalTier, TextGrid

from textgrid_utils.globals import ExecutionResult
from textgrid_utils.intervals.boundary_fixing import fix_interval_boundaries
from textgrid_utils.validation import InvalidGridError, ValidationError


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


def merge_grids(grids: List[TextGrid]) -> Tuple[ExecutionResult, Optional[TextGrid]]:
  assert len(grids) > 0

  if len(grids) == 1:
    return (None, False), grids[0]

  ref_grid = grids[0]

  for grid in grids:
    if error := InvalidGridError.validate(grid):
      return (error, False), None

    # if error := MultipleTiersWithThatNameError.validate(grid, ref_grid):
    #  return error, False

    if error := TiersNotSameError.validate(grid, ref_grid):
      return (error, False), None

  target_tiers = OrderedDict((
    (tier.name, tier.intervals)
    for tier in cast(List[IntervalTier], ref_grid.tiers)
  ))

  for grid in grids[1:]:
    for tier in cast(List[IntervalTier], ref_grid.tiers):
      target_tiers[tier.name].extend(tier.intervals)

  result = TextGrid()
  for tier, intervals in target_tiers.items():
    set_times_from_durations(intervals, 0.0)
    grid_tier = IntervalTier(
      tier, 0.0, intervals[-1].maxTime
    )
    grid_tier.intervals = intervals
    result.append(grid_tier)
  result.minTime = 0.0
  result.maxTime = result.tiers[0].maxTime

  if len(target_tiers) > 1:
    tier_names = list(target_tiers.keys())
    fix_interval_boundaries(result, grid.tiers[0].name, tier_names[1:], inf)
  return (None, True), result


def set_times_from_durations(intervals: Iterable[Interval], init_min_time: float) -> None:
  last_time = init_min_time
  for interval in intervals:
    duration = interval.duration()
    interval.minTime = last_time
    interval.maxTime = last_time + duration
    last_time = interval.maxTime
