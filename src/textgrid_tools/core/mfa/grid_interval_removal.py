from logging import getLogger
from typing import Iterable, List, Set, cast

import numpy as np
from audio_utils.audio import s_to_samples
from textgrid.textgrid import Interval, IntervalTier, TextGrid
from textgrid_tools.core.mfa.grid_audio_syncronization import (
    can_set_end_to_audio_len, set_end_to_audio_len)
from textgrid_tools.core.mfa.helper import (
    check_is_valid_grid, check_timepoints_exist_on_all_tiers_as_boundaries,
    find_intervals_with_mark, get_boundary_timepoints_from_intervals,
    get_boundary_timepoints_from_tier, get_first_tier,
    get_intervals_from_timespan, set_precision_interval, tier_exists)
from textgrid_tools.core.mfa.interval_boundary_adjustment import fix_timepoint
from tqdm import tqdm


def can_remove_intervals(grid: TextGrid, audio: np.ndarray, sr: int, reference_tier: str, remove_marks: Set[str], remove_empty: bool) -> bool:
  logger = getLogger(__name__)

  if not check_is_valid_grid(grid):
    logger.error("Grid is invalid!")
    return False

  if len(remove_marks) == 0 and not remove_empty:
    logger.info("Marks and/or remove_empty needs to be set!")
    return False

  if s_to_samples(grid.maxTime, sr) != audio.shape[0]:
    logger.error(
      f"Audio length and grid length does not match ({audio.shape[0]} vs. {s_to_samples(grid.maxTime, sr)})")
    return False
    # audio_len = samples_to_s(audio.shape[0], sr)
    # set_maxTime(grid, audio_len)

  if not tier_exists(grid, reference_tier):
    logger.error(f"Tier \"{reference_tier}\" not found!")
    return False

  ref_tier = get_first_tier(grid, reference_tier)
  ref_intervals_to_remove = list(find_intervals_with_mark(ref_tier, remove_marks, remove_empty))
  timepoints = get_boundary_timepoints_from_intervals(ref_intervals_to_remove)

  all_tiers_share_timepoints = check_timepoints_exist_on_all_tiers_as_boundaries(
    timepoints, grid.tiers)
  if not all_tiers_share_timepoints:
    logger.error("Not all tiers share the same interval boundaries at the deletion intervals!")
    return False

  return True


def remove_intervals(grid: TextGrid, audio: np.ndarray, sr: int, reference_tier_name: str, remove_marks: Set[str], remove_empty: bool, n_digits: int) -> np.ndarray:
  assert can_remove_intervals(grid, audio, sr, reference_tier_name, remove_marks, remove_empty)
  logger = getLogger(__name__)

  ref_tier = get_first_tier(grid, reference_tier_name)

  ref_intervals_to_remove = list(find_intervals_with_mark(ref_tier, remove_marks, remove_empty))

  for tier in cast(Iterable[IntervalTier], tqdm(grid.tiers)):
    for ref_interval_to_remove in ref_intervals_to_remove:
      for interval_on_tier in get_intervals_on_tier(ref_interval_to_remove, tier):
        tier.removeInterval(interval_on_tier)
    if len(tier.intervals) > 0:
      move_interval(tier.intervals[0], 0, n_digits)
      set_times_consecutively_tier(tier, n_digits)

  sync_timepoints = get_boundary_timepoints_from_tier(ref_tier)
  for tier in cast(Iterable[IntervalTier], tqdm(grid.tiers)):
    if tier == ref_tier:
      continue
    for timepoint in sync_timepoints:
      fix_timepoint(timepoint, tier, threshold=None)

  all_tiers_share_timepoints = check_timepoints_exist_on_all_tiers_as_boundaries(
    sync_timepoints, grid.tiers)
  assert all_tiers_share_timepoints

  assert grid.minTime <= ref_tier.minTime
  assert ref_tier.maxTime <= grid.maxTime
  grid.minTime = ref_tier.minTime
  grid.maxTime = ref_tier.maxTime
  assert check_is_valid_grid(grid)

  logger.info("Remove intervals from audio...")
  remove_range = []
  for ref_interval_to_remove in reversed(ref_intervals_to_remove):
    start = s_to_samples(ref_interval_to_remove.minTime, sr)
    end = s_to_samples(ref_interval_to_remove.maxTime, sr)
    assert end <= audio.shape[0]
    r = range(start, end)
    remove_range.extend(r)
  res_audio = np.delete(audio, remove_range, axis=0)

  # after multiple removals in audio some difference occurs
  can_set = can_set_end_to_audio_len(grid, res_audio, sr, n_digits)
  if not can_set:
    logger.exception("Couldn't set grid maxTime to audio len!")
    raise Exception()

  set_end_to_audio_len(grid, res_audio, sr, n_digits)

  removed_duration = sum(interval.duration() for interval in ref_intervals_to_remove)
  logger.info(f"Removed {len(ref_intervals_to_remove)} intervals ({removed_duration:.2f}s).")

  return res_audio


def get_intervals_on_tier(interval: Interval, tier: IntervalTier) -> List[Interval]:
  result = list(get_intervals_from_timespan(tier, interval.minTime, interval.maxTime))
  assert len(result) > 0
  assert result[0].minTime == interval.minTime
  assert result[-1].maxTime == interval.maxTime
  return result


def set_times_consecutively_tier(tier: IntervalTier, n_digits: int):
  set_times_consecutively_intervals(tier.intervals, n_digits)

  if len(tier.intervals) > 0:
    if cast(Interval, tier.intervals[0]).minTime != tier.minTime:
      tier.minTime = cast(Interval, tier.intervals[0]).minTime

    if cast(Interval, tier.intervals[-1]).maxTime != tier.maxTime:
      tier.maxTime = cast(Interval, tier.intervals[-1]).maxTime


def set_times_consecutively_intervals(intervals: List[Interval], n_digits: int):
  # could be the case that inprecisions are induced e.g. 0.95000000000000002
  for i in range(1, len(intervals)):
    prev_interval = cast(Interval, intervals[i - 1])
    current_interval = cast(Interval, intervals[i])
    gap_exists = current_interval.minTime != prev_interval.maxTime
    if gap_exists:
      assert prev_interval.maxTime < current_interval.minTime
      move_interval(current_interval, prev_interval.maxTime, n_digits)


def move_interval(interval: Interval, new_minTime: float, n_digits: int) -> None:
  duration = interval.duration()
  interval.minTime = new_minTime
  interval.maxTime = interval.minTime + duration
  set_precision_interval(interval, n_digits)
