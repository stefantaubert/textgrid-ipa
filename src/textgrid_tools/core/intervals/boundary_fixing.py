from logging import getLogger
from typing import Iterable, Optional, Set, Tuple, cast

from textgrid.textgrid import Interval, IntervalTier, TextGrid
from textgrid_tools.core.globals import ChangedAnything, ExecutionResult
from textgrid_tools.core.helper import (check_is_valid_grid, get_all_tiers,
                                        get_boundary_timepoints_from_tier,
                                        get_interval_from_maxTime,
                                        get_interval_from_minTime,
                                        get_single_tier,
                                        timepoint_is_boundary)
from textgrid_tools.core.validation import (InvalidGridError,
                                            MultipleTiersWithThatNameError,
                                            NonDistinctTiersError,
                                            NotExistingTierError,
                                            ValidationError)
from tqdm import tqdm


class ThresholdTooLowError(ValidationError):
  def __init__(self, threshold: float) -> None:
    super().__init__()
    self.threshold = threshold

  @classmethod
  def validate(cls, threshold: float):
    if not threshold > 0:
      return cls(threshold)
    return None

  @property
  def default_message(self) -> str:
    return f"Threshold needs to be greater than zero but was \"{self.threshold}\"!"


def fix_interval_boundaries(grid: TextGrid, reference_tier_name: str, tier_names: Set[str], difference_threshold: float) -> ExecutionResult:
  assert len(tier_names) > 0

  if error := InvalidGridError.validate(grid):
    return error, False

  if error := NotExistingTierError.validate(grid, reference_tier_name):
    return error, False

  if error := MultipleTiersWithThatNameError.validate(grid, reference_tier_name):
    return error, False

  if error := ThresholdTooLowError.validate(difference_threshold):
    return error, False

  for tier_name in tier_names:
    if error := NotExistingTierError.validate(grid, tier_name):
      return error, False

    if error := NonDistinctTiersError.validate(tier_name, reference_tier_name):
      return error, False

  logger = getLogger(__name__)

  ref_tier = get_single_tier(grid, reference_tier_name)

  synchronize_timepoints = list(get_boundary_timepoints_from_tier(ref_tier))

  tiers = list(get_all_tiers(grid, tier_names))

  total_success = True
  total_changed_anything = False
  for tier in cast(Iterable[IntervalTier], tqdm(tiers, desc="Tier", position=0, unit="t")):
    logger.info(f"Fixing tier {tier.name} ...")
    for timepoint in tqdm(synchronize_timepoints, desc="Interval", position=1, unit="in"):
      success, changed_anything = fix_timepoint(timepoint, tier, difference_threshold)
      total_success &= success
      total_changed_anything |= changed_anything

      if not success:
        logger.info("Not all boundaries could be fixed")

      if not changed_anything:
        logger.info("Did not changed anything!")

  if total_success:
    logger.info("Successfully fixed all boundaries from all tiers!")
  else:
    logger.info("Not all boundaries from all tiers could be fixed!")

  # nothing should not be changed a priori
  assert grid.minTime == ref_tier.minTime
  assert grid.maxTime == ref_tier.maxTime
  assert check_is_valid_grid(grid)

  return None, total_changed_anything


def fix_timepoint(timepoint: float, tier: IntervalTier, threshold: float) -> Tuple[bool, ChangedAnything]:
  is_already_fixed = timepoint_is_boundary(timepoint, tier)
  if is_already_fixed:
    return True, False

  interval = get_interval_from_time(tier, timepoint)
  prev_interval = get_interval_from_maxTime(tier, interval.minTime)
  next_interval = get_interval_from_minTime(tier, interval.maxTime)
  fixed, changed_anything = fix_timepoint_interval(
    timepoint, prev_interval, interval, next_interval, threshold)

  if changed_anything:
    is_first_interval = prev_interval is None
    if is_first_interval and tier.minTime != interval.minTime:
      tier.minTime = interval.minTime
    is_last_interval = next_interval is None
    if is_last_interval and tier.maxTime != interval.maxTime:
      tier.maxTime = interval.maxTime

  return fixed, changed_anything


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


def fix_timepoint_interval(timepoint: float, prev_interval: Optional[Interval], interval: Interval, next_interval: Optional[Interval], threshold: float) -> Tuple[bool, ChangedAnything]:
  assert interval.minTime <= timepoint < interval.maxTime
  logger = getLogger(__name__)

  minTime_difference = timepoint - interval.minTime
  maxTime_difference = interval.maxTime - timepoint
  assert minTime_difference >= 0
  assert maxTime_difference > 0

  if minTime_difference == 0:
    # logger.info(f"Interval [{interval.minTime}, {interval.maxTime}]: Nothing to change.")
    return True, False

  changed_anything = False
  fixed = True
  # minTime is before interval
  minTime_is_more_near = minTime_difference < maxTime_difference
  maxTime_is_more_near = maxTime_difference < minTime_difference
  if minTime_is_more_near:
    if minTime_difference <= threshold:
      # move starting forward
      logger.info(
        f"Interval [{interval.minTime}, {interval.maxTime}]: Set minTime to {timepoint} (+{minTime_difference}).")
      interval.minTime = timepoint
      changed_anything = True
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
      changed_anything = True
      if next_interval is not None:
        next_interval.minTime = timepoint
    else:
      fixed = False
      logger.info(
        f"Interval [{interval.minTime}, {interval.maxTime}]: Didn't set maxTime to {timepoint} (-{maxTime_difference}).")
  else:
    assert minTime_difference == maxTime_difference
    if minTime_difference <= threshold:
      # both have same difference, move starting forward
      logger.info(
        f"Interval [{interval.minTime}, {interval.maxTime}]: Set minTime to {timepoint} (+{minTime_difference}).")
      interval.minTime = timepoint
      changed_anything = True
      if prev_interval is not None:
        prev_interval.maxTime = timepoint
    else:
      fixed = False
      logger.info(
        f"Interval [{interval.minTime}, {interval.maxTime}]: Didn't set minTime to {timepoint} (+{minTime_difference}).")
  return fixed, changed_anything
