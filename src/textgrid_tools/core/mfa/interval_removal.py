from logging import getLogger
from typing import Set

import numpy as np
from audio_utils.audio import s_to_samples
from textgrid.textgrid import IntervalTier, TextGrid
from textgrid_tools.core.mfa.helper import (
    check_is_valid_grid, check_timepoints_exist_on_all_tiers,
    find_intervals_with_mark, get_boundary_timepoints_from_intervals,
    get_intervals_from_timespan, set_times_consecutively_tier)


def remove_intervals(grid: TextGrid, audio: np.ndarray, sr: int, reference_tier_name: str, remove_marks: Set[str]) -> np.ndarray:
  assert check_is_valid_grid(grid)
  logger = getLogger(__name__)

  ref_tier: IntervalTier = grid.getFirst(reference_tier_name)
  if ref_tier is None:
    logger.exception("Tier not found!")
    raise Exception()

  remove = list(find_intervals_with_mark(ref_tier, remove_marks))
  timepoints = get_boundary_timepoints_from_intervals(remove)

  all_tiers_share_timepoints = check_timepoints_exist_on_all_tiers(timepoints, grid.tiers)
  if not all_tiers_share_timepoints:
    return

  for tier in grid.tiers:
    for interval in remove:
      remove_intervals_from_boundary(tier, interval.minTime, interval.maxTime)

  logger.info("Remove intervals from audio...")
  remove_range = []
  for interval in reversed(remove):
    start = s_to_samples(interval.minTime, sr)
    end = s_to_samples(interval.maxTime, sr)
    r = range(start, end)
    remove_range.extend(r)
  res_audio = np.delete(audio, remove_range, axis=0)

  for tier in grid.tiers:
    set_times_consecutively_tier(tier, keep_duration=True)

  # minTime should not be changed a priori
  assert grid.minTime <= ref_tier.minTime
  assert ref_tier.maxTime <= grid.maxTime
  grid.minTime = ref_tier.minTime
  grid.maxTime = ref_tier.maxTime
  return res_audio


def remove_intervals_from_boundary(tier: IntervalTier, minTime: float, maxTime: float) -> None:
  intervals_to_remove = list(get_intervals_from_timespan(
      tier, minTime, maxTime))
  assert len(intervals_to_remove) > 0
  assert intervals_to_remove[0].minTime == minTime
  assert intervals_to_remove[-1].maxTime == maxTime
  for interval in intervals_to_remove:
    tier.removeInterval(interval)
