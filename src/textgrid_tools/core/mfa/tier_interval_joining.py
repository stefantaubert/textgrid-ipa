from logging import getLogger
from typing import List, Tuple, cast

from textgrid.textgrid import Interval, IntervalTier, TextGrid
from textgrid_tools.core.mfa.helper import (check_is_valid_grid,
                                            interval_is_empty, tier_exists)
from textgrid_tools.utils import durations_to_intervals, update_or_add_tier


def can_join_intervals(grid: TextGrid, tier: str, new_tier: str, min_pause_s: float, overwrite_tier: bool) -> None:
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

  if min_pause_s <= 0:
    logger.error(f"Min pause needs to be > 0!")
    return False

  return True


def join_intervals(grid: TextGrid, tier: str, new_tier: str, min_pause_s: float, overwrite_tier: bool) -> None:
  assert can_join_intervals(grid, tier, new_tier,
                            min_pause_s, overwrite_tier)
  new_tier = IntervalTier(
    name=new_tier,
    minTime=grid.minTime,
    maxTime=grid.maxTime,
  )

  reference_tier = cast(IntervalTier, grid.getFirst(tier))

  durations: List[Tuple[str, float]] = []
  current_batch = []
  current_duration = 0
  interval: Interval
  for interval in reference_tier.intervals:
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

  intervals = durations_to_intervals(durations, maxTime=grid.maxTime)
  new_tier.intervals.extend(intervals)

  grid.append(new_tier)

  if overwrite_tier:
    update_or_add_tier(grid, new_tier)
  else:
    grid.append(new_tier)
