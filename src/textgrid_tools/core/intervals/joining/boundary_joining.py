from logging import getLogger
from typing import Generator, List, Optional

from text_utils import StringFormat
from textgrid.textgrid import Interval, IntervalTier, TextGrid
from textgrid_tools.core.mfa.helper import (
    check_is_valid_grid, check_timepoints_exist_on_all_tiers_as_boundaries,
    get_boundary_timepoints_from_tier, get_first_tier,
    get_intervals_part_of_timespan, merge_intervals, replace_tier, tier_exists)
from textgrid_tools.core.mfa.interval_format import IntervalFormat


def can_join_intervals(grid: TextGrid, tier_name: str, boundary_tier_name: str, output_tier_name: Optional[str], overwrite_tier: bool) -> None:
  logger = getLogger(__name__)

  if not check_is_valid_grid(grid):
    logger.error("Grid is invalid!")
    return False

  if not tier_exists(grid, tier_name):
    logger.error(f"Tier \"{tier_name}\" not found!")
    return False

  if not tier_exists(grid, boundary_tier_name):
    logger.error(f"Tier \"{boundary_tier_name}\" not found!")
    return False

  tier = get_first_tier(grid, tier_name)
  boundary_tier = get_first_tier(grid, boundary_tier_name)
  boundary_tier_timepoints = get_boundary_timepoints_from_tier(boundary_tier)
  tier_share_timepoints_from_boundary = check_timepoints_exist_on_all_tiers_as_boundaries(
    boundary_tier_timepoints, [tier])

  if not tier_share_timepoints_from_boundary:
    logger.error(f"Not all boundaries of tier \"{boundary_tier}\" exist on tier \"{tier}\"!")
    return False

  if output_tier_name is None:
    output_tier_name = tier_name

  if tier_exists(grid, output_tier_name) and not overwrite_tier:
    logger.error(f"Tier \"{output_tier_name}\" already exists!")
    return False

  return True


def join_intervals(grid: TextGrid, tier_name: str, tier_string_format: StringFormat, tier_interval_format: IntervalFormat, boundary_tier_name: str, output_tier_name: Optional[str] = None, overwrite_tier: bool = True) -> None:
  assert can_join_intervals(grid, tier_name, boundary_tier_name, output_tier_name, overwrite_tier)

  if output_tier_name is None:
    output_tier_name = tier_name

  tier = get_first_tier(grid, tier_name)
  boundary_tier = get_first_tier(grid, boundary_tier_name)

  new_tier = IntervalTier(
    name=output_tier_name,
    minTime=grid.minTime,
    maxTime=grid.maxTime,
  )

  chunked_intervals = chunk_intervals(tier, boundary_tier)

  for chunk in chunked_intervals:
    interval = merge_intervals(chunk, tier_string_format, tier_interval_format)
    new_tier.addInterval(interval)

  if overwrite_tier and tier.name == new_tier.name:
    replace_tier(tier, new_tier)
  elif overwrite_tier and tier_exists(grid, new_tier.name):
    existing_tier = get_first_tier(grid, new_tier.name)
    replace_tier(existing_tier, new_tier)
  else:
    grid.append(new_tier)


def chunk_intervals(tier: IntervalTier, boundary_tier: IntervalTier) -> Generator[List[Interval], None, None]:
  synchronize_timepoints = get_boundary_timepoints_from_tier(boundary_tier)

  for i in range(1, len(synchronize_timepoints)):
    last_timepoint = synchronize_timepoints[i - 1]
    current_timepoint = synchronize_timepoints[i]
    tier_intervals_in_range = list(get_intervals_part_of_timespan(
      tier, last_timepoint, current_timepoint))
    yield tier_intervals_in_range
