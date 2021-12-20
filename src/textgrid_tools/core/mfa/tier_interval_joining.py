from enum import IntEnum
from logging import getLogger
from typing import List, Optional, Tuple, cast

from textgrid.textgrid import Interval, IntervalTier, TextGrid
from textgrid_tools.core.mfa.helper import (
    check_is_valid_grid, check_timepoints_exist_on_all_tiers_as_boundaries,
    get_boundary_timepoints_from_tier, get_first_tier,
    get_intervals_part_of_timespan, interval_is_empty, intervals_to_text,
    tier_exists, tier_to_text)
from textgrid_tools.core.mfa.string_format import StringFormat
from textgrid_tools.utils import durations_to_intervals, update_or_add_tier


class JoinMode(IntEnum):
  TIER = 0
  BOUNDARY = 1
  PAUSE = 2


def can_join_intervals(grid: TextGrid, tier: str, new_tier: str, min_pause_s: Optional[float], boundary_tier: Optional[str], mode: JoinMode, overwrite_tier: bool) -> None:
  logger = getLogger(__name__)

  if not check_is_valid_grid(grid):
    logger.error("Grid is invalid!")
    return False

  if not tier_exists(grid, tier):
    logger.error(f"Tier \"{tier}\" not found!")
    return False

  if tier_exists(grid, new_tier) and not overwrite_tier:
    logger.error(f"Tier \"{new_tier}\" already exists!")
    return False

  if mode == JoinMode.BOUNDARY:
    if boundary_tier is None:
      logger.error("No reference tier defined!")
      return False

    if not tier_exists(grid, boundary_tier):
      logger.error(f"Reference tier \"{boundary_tier}\" not found!")
      return False

    tier_instance = get_first_tier(grid, tier)
    b_tier = get_first_tier(grid, boundary_tier)
    synchronize_timepoints = get_boundary_timepoints_from_tier(b_tier)

    all_tiers_share_timepoints = check_timepoints_exist_on_all_tiers_as_boundaries(
      synchronize_timepoints, [tier_instance])

    if not all_tiers_share_timepoints:
      logger.error(f"Not all boundaries of tier \"{boundary_tier}\" exist on tier \"{tier}\"!")
      return False

  if mode == JoinMode.TIER:
    pass

  if mode == JoinMode.PAUSE:
    if min_pause_s is None:
      logger.error("No min pause defined!")
      return False

    if min_pause_s <= 0:
      logger.error("Min pause needs to be > 0!")
      return False

  return True


def join_intervals(grid: TextGrid, tier: str, tier_string_format: StringFormat, new_tier: str, min_pause_s: Optional[float], boundary_tier: Optional[str], mode: JoinMode, overwrite_tier: bool) -> None:
  assert can_join_intervals(grid, tier, new_tier,
                            min_pause_s, boundary_tier, mode, overwrite_tier)

  tier_instance = get_first_tier(grid, tier)

  new_tier_instance = IntervalTier(
    name=new_tier,
    minTime=grid.minTime,
    maxTime=grid.maxTime,
  )

  if mode == JoinMode.PAUSE:
    durations = join_via_pause(tier_instance, min_pause_s)
    intervals = durations_to_intervals(durations, maxTime=grid.maxTime)
    new_tier_instance.intervals.extend(intervals)
  elif mode == JoinMode.TIER:
    text = tier_to_text(tier_instance, join_with=tier_string_format.get_word_separator())
    interval = Interval(
      minTime=grid.minTime,
      maxTime=grid.maxTime,
      mark=text,
    )
    new_tier_instance.addInterval(interval)
  elif mode == JoinMode.BOUNDARY:
    b_tier = get_first_tier(grid, boundary_tier)

    synchronize_timepoints = get_boundary_timepoints_from_tier(b_tier)

    for i in range(1, len(synchronize_timepoints)):
      last_timepoint = synchronize_timepoints[i - 1]
      current_timepoint = synchronize_timepoints[i]
      tier_intervals_in_range = list(get_intervals_part_of_timespan(
        tier_instance, last_timepoint, current_timepoint))
      sep = tier_string_format.get_word_separator()
      # TODO join right!
      content = intervals_to_text(tier_intervals_in_range, join_with=sep)
      new_interval = Interval(
        minTime=last_timepoint,
        maxTime=current_timepoint,
        mark=content,
      )
      new_tier_instance.addInterval(new_interval)
  else:
    assert False

  if overwrite_tier:
    update_or_add_tier(grid, new_tier_instance)
  else:
    grid.append(new_tier)


def join_via_pause(tier: IntervalTier, min_pause_s: float) -> List[Tuple[str, float]]:
  durations: List[Tuple[str, float]] = []
  current_batch = []
  current_duration = 0
  interval: Interval
  for interval in tier.intervals:
    is_empty = interval_is_empty(interval)
    if is_empty:
      if interval.duration() < min_pause_s:
        current_duration += interval.duration()
      else:
        if len(current_batch) > 0:
          batch_str = " ".join(current_batch)
          durations.append((batch_str, current_duration))
          current_batch.clear()
          current_duration = 0
        durations.append((interval.mark, interval.duration()))
    else:
      current_batch.append(interval.mark)
      current_duration += interval.duration()

  if len(current_batch) > 0:
    batch_str = " ".join(current_batch)
    durations.append((batch_str, current_duration))

  return durations
