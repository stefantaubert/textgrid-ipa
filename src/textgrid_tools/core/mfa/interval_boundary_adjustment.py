from logging import getLogger
from typing import Iterable, Optional, cast

from textgrid.textgrid import Interval, IntervalTier, TextGrid
from textgrid_tools.core.mfa.helper import (check_is_valid_grid,
                                            get_boundary_timepoints_from_tier, get_interval_from_maxTime, get_interval_from_minTime, get_interval_from_time)
from tqdm import tqdm


def fix_interval_boundaries_grid(grid: TextGrid, reference_tier_name: str, difference_threshold: float):
  assert check_is_valid_grid(grid)

  logger = getLogger(__name__)

  ref_tier: IntervalTier = grid.getFirst(reference_tier_name)
  if ref_tier is None:
    logger.exception("Tier not found!")
    raise Exception()

  synchronize_timepoints = list(get_boundary_timepoints_from_tier(ref_tier))

  for tier in cast(Iterable[IntervalTier], tqdm(grid.tiers, desc="Tier", position=0, unit="t")):
    if tier == ref_tier:
      continue
    logger.info(f"Fixing tier {tier.name}...")
    total_success = True
    for timepoint in tqdm(synchronize_timepoints, desc="Interval", position=1, unit="in"):
      success = fix_timepoint(timepoint, tier, difference_threshold)
      total_success &= success
      if not success:
        logger.info("Not all boundaries could be fixed")
  if total_success:
    logger.info("All tiers: Successfully fixed all boundaries!")
  else:
    logger.info("All tiers: Not all boundaries could be fixed!")

  # nothing should not be changed a priori
  assert grid.minTime == ref_tier.minTime
  assert grid.maxTime == ref_tier.maxTime
  assert check_is_valid_grid(grid)
  # todo also change len if audio len is different


def fix_timepoint(timepoint: float, tier: IntervalTier, threshold: float) -> bool:
  interval = get_interval_from_time(tier, timepoint)
  assert interval is not None
  prev_interval = get_interval_from_maxTime(tier, interval.minTime)
  next_interval = get_interval_from_minTime(tier, interval.maxTime)
  return fix_timepoint_interval(timepoint, prev_interval, interval, next_interval, threshold)


def fix_timepoint_interval(timepoint: float, prev_interval: Optional[Interval], interval: Interval, next_interval: Optional[Interval], threshold: float) -> bool:
  assert interval.minTime <= timepoint
  assert interval.maxTime > timepoint
  logger = getLogger(__name__)
  fixed = True

  minTime_difference = timepoint - interval.minTime
  maxTime_difference = interval.maxTime - timepoint
  assert minTime_difference >= 0
  assert maxTime_difference > 0

  if minTime_difference == 0:
    # logger.info(f"Interval [{interval.minTime}, {interval.maxTime}]: Nothing to change.")
    return fixed

  # minTime is before interval
  minTime_is_more_near = minTime_difference < maxTime_difference
  maxTime_is_more_near = maxTime_difference < minTime_difference
  if minTime_is_more_near:
    if minTime_difference <= threshold:
      # move starting forward
      logger.info(
        f"Interval [{interval.minTime}, {interval.maxTime}]: Set minTime to {timepoint} (+{minTime_difference}).")
      interval.minTime = timepoint
      if prev_interval is not None:
        prev_interval.maxTime = timepoint
    else:
      fixed = False
      logger.info(
        f"Interval [{interval.minTime}, {interval.maxTime}]: Didn't set minTime to {timepoint} (+{minTime_difference}).")
  elif maxTime_is_more_near:
    if maxTime_difference <= threshold:
      # move ending backward, outside of the boundaries
      logger.info(
        f"Interval [{interval.minTime}, {interval.maxTime}]: Set maxTime to {timepoint} (-{maxTime_difference}).")
      interval.maxTime = timepoint
      if next_interval is not None:
        next_interval.minTime = timepoint
    else:
      fixed = False
      logger.info(
        f"Interval [{interval.minTime}, {interval.maxTime}]: Didn't set maxTime to {timepoint} (-{maxTime_difference}).")
  else:
    if minTime_difference <= threshold:
      # both have same difference, move starting forward
      logger.info(
        f"Interval [{interval.minTime}, {interval.maxTime}]: Set minTime to {timepoint} (+{minTime_difference}).")
      interval.minTime = timepoint
      if prev_interval is not None:
        prev_interval.maxTime = timepoint
    else:
      fixed = False
      logger.info(
        f"Interval [{interval.minTime}, {interval.maxTime}]: Didn't set minTime to {timepoint} (+{minTime_difference}).")
  return fixed
