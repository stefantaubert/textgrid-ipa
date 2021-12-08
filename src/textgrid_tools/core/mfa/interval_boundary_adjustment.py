from logging import getLogger
from typing import Iterable, Optional, cast

from textgrid.textgrid import Interval, IntervalTier, TextGrid
from textgrid_tools.core.mfa.helper import (check_is_valid_grid,
                                            get_boundary_timepoints_from_tier,
                                            get_interval_from_maxTime,
                                            get_interval_from_minTime,
                                            timepoint_is_boundary)
from tqdm import tqdm


def fix_interval_boundaries_grid(grid: TextGrid, reference_tier_name: str, difference_threshold: Optional[float]) -> bool:
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
  return total_success


def fix_timepoint(timepoint: float, tier: IntervalTier, threshold: Optional[float]) -> bool:
  is_already_fixed = timepoint_is_boundary(timepoint, tier)
  if is_already_fixed:
    return True
  interval = get_interval_from_time(tier, timepoint)
  prev_interval = get_interval_from_maxTime(tier, interval.minTime)
  next_interval = get_interval_from_minTime(tier, interval.maxTime)
  fixed = fix_timepoint_interval(timepoint, prev_interval, interval, next_interval, threshold)
  if prev_interval is None and tier.minTime != interval.minTime:
    tier.minTime = interval.minTime
  if next_interval is None and tier.maxTime != interval.maxTime:
    tier.maxTime = interval.maxTime
  return fixed


def get_interval_from_time(tier: IntervalTier, time: float) -> Interval:
  assert len(tier.intervals) > 0
  for interval in cast(Iterable[Interval], tier.intervals):
    if interval.minTime <= time < interval.maxTime:
      return interval
  if time < tier.intervals[0].minTime:
    return tier.intervals[0]
  if time >= tier.intervals[-1].maxTime:
    return tier.intervals[-1]
  assert False


def fix_timepoint_interval(timepoint: float, prev_interval: Optional[Interval], interval: Interval, next_interval: Optional[Interval], threshold: Optional[float]) -> bool:
  assert interval.minTime <= timepoint < interval.maxTime
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
    if threshold is None or minTime_difference <= threshold:
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
    if threshold is None or maxTime_difference <= threshold:
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
    if threshold is None or minTime_difference <= threshold:
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
