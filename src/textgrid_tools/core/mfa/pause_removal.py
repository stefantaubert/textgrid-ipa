from logging import getLogger
from typing import List, Tuple, cast

from textgrid.textgrid import Interval, IntervalTier, TextGrid
from textgrid_tools.core.mfa.helper import interval_is_empty
from textgrid_tools.utils import durations_to_intervals, update_or_add_tier


def merge_words_together(grid: TextGrid, reference_tier_name: str, new_tier_name: str, min_pause_s: float, overwrite_existing_tier: bool) -> None:
  logger = getLogger(__name__)

  new_tier = grid.getFirst(new_tier_name)
  if new_tier is not None and not overwrite_existing_tier:
    logger.error("Tier already exists!")
    return

  new_tier = IntervalTier(
    name=new_tier_name,
    minTime=grid.minTime,
    maxTime=grid.maxTime,
  )

  reference_tier = cast(IntervalTier, grid.getFirst(reference_tier_name))

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

  if overwrite_existing_tier:
    update_or_add_tier(grid, new_tier)
  else:
    grid.append(new_tier)
  return
