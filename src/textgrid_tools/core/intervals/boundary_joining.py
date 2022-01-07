from typing import Generator, List, Set

from ordered_set import OrderedSet
from text_utils import StringFormat
from textgrid.textgrid import Interval, IntervalTier, TextGrid
from textgrid_tools.core.comparison import check_intervals_are_equal
from textgrid_tools.core.globals import ExecutionResult
from textgrid_tools.core.intervals.common import (merge_intervals,
                                                  replace_intervals)
from textgrid_tools.core.helper import (get_all_tiers,
                                        get_boundary_timepoints_from_tier,
                                        get_intervals_part_of_timespan,
                                        get_single_tier)
from textgrid_tools.core.interval_format import IntervalFormat
from textgrid_tools.core.validation import (BoundaryError, InvalidGridError,
                                            InvalidStringFormatIntervalError,
                                            MultipleTiersWithThatNameError,
                                            NonDistinctTiersError,
                                            NotExistingTierError,
                                            NotMatchingIntervalFormatError)


def join_intervals(grid: TextGrid, boundary_tier_name: str, tier_names: Set[str], tiers_string_format: StringFormat, tiers_interval_format: IntervalFormat) -> ExecutionResult:
  assert len(tier_names) > 0

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

  for tier in tiers:
    if error := InvalidStringFormatIntervalError.validate_tier(tier, tiers_string_format):
      return error, False

    if error := NotMatchingIntervalFormatError.validate(tier, tiers_interval_format, tiers_string_format):
      return error, False

  changed_anything = False
  for tier in tiers:
    for chunk in chunk_intervals(tier, boundary_tier_timepoints):
      merged_interval = merge_intervals(chunk, tiers_string_format, tiers_interval_format)
      if not check_intervals_are_equal(chunk, [merged_interval]):
        replace_intervals(tier, chunk, [merged_interval])
        changed_anything = True

  return None, changed_anything


def chunk_intervals(tier: IntervalTier, synchronize_timepoints: OrderedSet[float]) -> Generator[List[Interval], None, None]:
  for i in range(1, len(synchronize_timepoints)):
    last_timepoint = synchronize_timepoints[i - 1]
    current_timepoint = synchronize_timepoints[i]
    tier_intervals_in_range = list(get_intervals_part_of_timespan(
      tier, last_timepoint, current_timepoint))
    yield tier_intervals_in_range
