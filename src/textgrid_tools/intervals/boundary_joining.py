from logging import Logger, getLogger
from typing import Generator, Iterable, List, Optional, Set, cast

from ordered_set import OrderedSet
from textgrid.textgrid import Interval, TextGrid

from textgrid_tools.comparison import check_intervals_are_equal
from textgrid_tools.globals import ExecutionResult
from textgrid_tools.helper import (get_all_tiers, get_boundary_timepoints_from_tier,
                                   get_intervals_part_of_timespan_from_intervals, get_single_tier)
from textgrid_tools.intervals.common import merge_intervals, replace_intervals
from textgrid_tools.validation import (BoundaryError, InvalidGridError,
                                       MultipleTiersWithThatNameError, NonDistinctTiersError,
                                       NotExistingTierError)


def join_intervals_on_boundaries(grid: TextGrid, boundary_tier_name: str, tier_names: Set[str], join_with: str, ignore_empty: bool, logger: Optional[Logger]) -> ExecutionResult:
  assert len(tier_names) > 0

  if logger is None:
    logger = getLogger(__name__)

  if error := InvalidGridError.validate(grid):
    return error, False

  if error := NotExistingTierError.validate(grid, boundary_tier_name):
    return error, False

  if error := MultipleTiersWithThatNameError.validate(grid, boundary_tier_name):
    return error, False

  for tier_name in tier_names:
    if error := NotExistingTierError.validate(grid, tier_name):
      return error, False

    if error := NonDistinctTiersError.validate(tier_name, boundary_tier_name):
      return error, False

  boundary_tier = get_single_tier(grid, boundary_tier_name)
  boundary_tier_timepoints = get_boundary_timepoints_from_tier(boundary_tier)
  tiers = list(get_all_tiers(grid, tier_names))

  if error := BoundaryError.validate(boundary_tier_timepoints, tiers):
    return error, False

  changed_anything = False
  for tier in tiers:
    intervals_copy = cast(Iterable[Interval], list(tier.intervals))
    for chunk in chunk_intervals(intervals_copy, boundary_tier_timepoints):
      merged_interval = merge_intervals(chunk, join_with, ignore_empty)
      if not check_intervals_are_equal(chunk, [merged_interval]):
        replace_intervals(tier, chunk, [merged_interval])
        changed_anything = True

  return None, changed_anything


def chunk_intervals(intervals: Iterable[Interval], synchronize_timepoints: OrderedSet[float]) -> Generator[List[Interval], None, None]:
  for i in range(1, len(synchronize_timepoints)):
    last_timepoint = synchronize_timepoints[i - 1]
    current_timepoint = synchronize_timepoints[i]
    tier_intervals_in_range = list(get_intervals_part_of_timespan_from_intervals(
      intervals, last_timepoint, current_timepoint))
    yield tier_intervals_in_range
