from logging import Logger, getLogger
from math import inf
from typing import Iterable, Optional, Set, Tuple, cast

from textgrid.textgrid import Interval, IntervalTier, TextGrid

from textgrid_tools.globals import ChangedAnything, ExecutionResult
from textgrid_tools.helper import (check_is_valid_grid, get_all_tiers,
                                   get_boundary_timepoints_from_tier, get_interval_from_maxTime,
                                   get_interval_from_minTime, get_single_tier,
                                   timepoint_is_boundary)
from textgrid_tools.validation import (InvalidGridError, MultipleTiersWithThatNameError,
                                       NonDistinctTiersError, NotExistingTierError)


def fix_interval_boundaries(grid: TextGrid, reference_tier_name: str, tier_names: Set[str], difference_threshold: float, logger: Optional[Logger]) -> ExecutionResult:
  assert len(tier_names) > 0
  assert difference_threshold > 0

  if logger is None:
    logger = getLogger(__name__)

  if error := InvalidGridError.validate(grid):
    return error, False

  if error := NotExistingTierError.validate(grid, reference_tier_name):
    return error, False

  if error := MultipleTiersWithThatNameError.validate(grid, reference_tier_name):
    return error, False

  for tier_name in tier_names:
    if error := NotExistingTierError.validate(grid, tier_name):
      return error, False

    if error := NonDistinctTiersError.validate(tier_name, reference_tier_name):
      return error, False

  if logger is None:
    logger = getLogger(__name__)

  ref_tier = get_single_tier(grid, reference_tier_name)

  synchronize_timepoints = list(get_boundary_timepoints_from_tier(ref_tier))

  tiers = list(get_all_tiers(grid, tier_names))

  total_success = True
  total_changed_anything = False
  for tier in cast(Iterable[IntervalTier], tiers):
    logger.info(f"Looking for boundaries to fix on tier \"{tier.name}\"")
    for timepoint in synchronize_timepoints:
      success, changed_anything = fix_timepoint(timepoint, tier, difference_threshold, logger)
      total_success &= success
      total_changed_anything |= changed_anything

      # if not success:
      #   logger.info("Not all boundaries could be fixed!")

      # if not changed_anything:
      #   logger.debug("Did not changed anything!")

  if total_success:
    if total_changed_anything:
      logger.info("Successfully fixed all boundaries from all tiers!")
    else:
      logger.info("Didn't changed anything!")
  else:
    logger.info("Not all boundaries from all tiers could be fixed!")

  # nothing should not be changed a priori
  assert grid.minTime == ref_tier.minTime
  assert grid.maxTime == ref_tier.maxTime
  assert check_is_valid_grid(grid)

  return None, total_changed_anything


def fix_timepoint(timepoint: float, tier: IntervalTier, threshold: float, logger: Logger) -> Tuple[bool, ChangedAnything]:
  is_already_fixed = timepoint_is_boundary(timepoint, tier)
  if is_already_fixed:
    return True, False

  interval = get_interval_from_time(tier, timepoint)
  prev_interval = get_interval_from_maxTime(tier, interval.minTime)
  next_interval = get_interval_from_minTime(tier, interval.maxTime)
  fixed, changed_anything = fix_timepoint_interval(
    timepoint, prev_interval, interval, next_interval, threshold, logger)

  if changed_anything:
    is_first_interval = prev_interval is None
    if is_first_interval and tier.minTime != interval.minTime:
      tier.minTime = interval.minTime
    is_last_interval = next_interval is None
    if is_last_interval and tier.maxTime != interval.maxTime:
      tier.maxTime = interval.maxTime

  return fixed, changed_anything


def get_interval_from_time(tier: IntervalTier, time: float) -> Interval:
  assert time >= 0
  assert time < inf
  assert len(tier.intervals) > 0
  for interval in cast(Iterable[Interval], tier.intervals):
    if interval.minTime <= time < interval.maxTime:
      return interval
  if time < tier.intervals[0].minTime:
    return tier.intervals[0]
  if time >= tier.intervals[-1].maxTime:
    return tier.intervals[-1]
  assert False


def fix_timepoint_interval(timepoint: float, prev_interval: Optional[Interval], interval: Interval, next_interval: Optional[Interval], threshold: float, logger: Logger) -> Tuple[bool, ChangedAnything]:
  assert timepoint >= 0
  assert timepoint < inf
  if timepoint > interval.maxTime and next_interval is None:
    difference = timepoint - interval.maxTime
    if difference < threshold:
      interval.maxTime = timepoint
      logger.info(
        f"Interval [{interval.minTime}, {interval.maxTime}]: Set maxTime to {timepoint} (+{difference} difference).")
      return True, True
    else:
      logger.info(
        f"Interval [{interval.minTime}, {interval.maxTime}]: Didn't set maxTime to {timepoint} (+{difference}).")
      return False, False

  if timepoint < interval.minTime and prev_interval is None:
    difference = interval.minTime - timepoint
    if difference < threshold:
      interval.minTime = timepoint
      logger.info(
        f"Interval [{interval.minTime}, {interval.maxTime}]: Set minTime to {timepoint} (-{difference} difference).")
      return True, True
    else:
      logger.info(
        f"Interval [{interval.minTime}, {interval.maxTime}]: Didn't set minTime to {timepoint} (-{difference}).")
      return False, False

  x = interval.minTime <= timepoint < interval.maxTime
  if not x:
    print("a")

  min_time_difference = timepoint - interval.minTime
  max_time_difference = interval.maxTime - timepoint
  assert min_time_difference >= 0
  assert max_time_difference > 0

  if min_time_difference == 0:
    # logger.info(f"Interval [{interval.minTime}, {interval.maxTime}]: Nothing to change.")
    return True, False

  changed_anything = False
  fixed = True
  # minTime is before interval
  min_time_is_nearer = min_time_difference < max_time_difference
  max_time_is_nearer = max_time_difference < min_time_difference

  if min_time_is_nearer:
    if min_time_difference <= threshold:
      # move starting forward
      logger.info(
        f"Interval [{interval.minTime}, {interval.maxTime}]: Set minTime to {timepoint} (+{min_time_difference}).")
      interval.minTime = timepoint
      changed_anything = True
      if prev_interval is not None:
        prev_interval.maxTime = timepoint
    else:
      fixed = False
      logger.info(
        f"Interval [{interval.minTime}, {interval.maxTime}]: Didn't set minTime to {timepoint} (+{min_time_difference}).")
  elif max_time_is_nearer:
    if max_time_difference <= threshold:
      # move ending backward, outside of the boundaries
      logger.info(
        f"Interval [{interval.minTime}, {interval.maxTime}]: Set maxTime to {timepoint} (-{max_time_difference}).")
      interval.maxTime = timepoint
      changed_anything = True
      if next_interval is not None:
        next_interval.minTime = timepoint
    else:
      fixed = False
      logger.info(
        f"Interval [{interval.minTime}, {interval.maxTime}]: Didn't set maxTime to {timepoint} (-{max_time_difference}).")
  else:
    assert min_time_difference == max_time_difference
    if min_time_difference <= threshold:
      # both have same difference, move starting forward
      logger.info(
        f"Interval [{interval.minTime}, {interval.maxTime}]: Set minTime to {timepoint} (+{min_time_difference}).")
      interval.minTime = timepoint
      changed_anything = True
      if prev_interval is not None:
        prev_interval.maxTime = timepoint
    else:
      fixed = False
      logger.info(
        f"Interval [{interval.minTime}, {interval.maxTime}]: Didn't set minTime to {timepoint} (+{min_time_difference}).")
  return fixed, changed_anything
