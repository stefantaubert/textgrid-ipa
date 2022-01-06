from logging import getLogger
from typing import Iterable, List, Optional, Set, Tuple, cast

import numpy as np
from audio_utils.audio import s_to_samples
from textgrid.textgrid import Interval, IntervalTier, TextGrid
from textgrid_tools.core.globals import ExecutionResult
from textgrid_tools.core.mfa.grid_audio_synchronization import (
    LastIntervalToShortError, set_end_to_audio_len)
from textgrid_tools.core.mfa.helper import (
    check_is_valid_grid, check_timepoints_exist_on_all_tiers_as_boundaries,
    find_intervals_with_mark, get_boundary_timepoints_from_intervals,
    get_boundary_timepoints_from_tier, get_first_tier, get_intervals_on_tier,
    set_precision_interval)
from textgrid_tools.core.mfa.interval_boundary_adjustment import fix_timepoint
from textgrid_tools.core.validation import (AudioAndGridLengthMismatchError,
                                            BoundaryError, InvalidGridError,
                                            NotExistingTierError,
                                            ValidationError)
from tqdm import tqdm


class NothingDefinedToRemoveError(ValidationError):
  @classmethod
  def validate(cls, remove_marks: Set[str], remove_empty: bool):
    if len(remove_marks) == 0 and not remove_empty:
      return cls()
    return None

  @property
  def default_message(self) -> str:
    return "Marks and/or remove_empty needs to be set!"


def remove_intervals(grid: TextGrid, audio: Optional[np.ndarray], sr: Optional[int], reference_tier_name: str, remove_marks: Set[str], remove_empty: bool, n_digits: int) -> Tuple[ExecutionResult, Optional[np.ndarray]]:
  assert n_digits >= 0
  if error := InvalidGridError.validate(grid):
    return (error, False), None

  if error := NothingDefinedToRemoveError.validate(remove_marks, remove_empty):
    return (error, False), None

  if error := NotExistingTierError.validate(grid, reference_tier_name):
    return (error, False), None

  if audio is not None:
    assert sr is not None
    if error := AudioAndGridLengthMismatchError.validate(grid, audio, sr):
      return (error, False), None

  logger = getLogger(__name__)

  ref_tier = get_first_tier(grid, reference_tier_name)

  ref_intervals_to_remove = list(find_intervals_with_mark(ref_tier, remove_marks, remove_empty))
  timepoints = get_boundary_timepoints_from_intervals(ref_intervals_to_remove)

  if error := BoundaryError.validate(timepoints, grid.tiers):
    return (error, False), None

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

  res_audio = None
  if audio is not None:
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
    if error := LastIntervalToShortError.validate(grid, res_audio, sr, n_digits):
      raise Exception()
      # return error, False

    set_end_to_audio_len(grid, res_audio, sr, n_digits)

  removed_duration = sum(interval.duration() for interval in ref_intervals_to_remove)
  logger.info(f"Removed {len(ref_intervals_to_remove)} intervals ({removed_duration:.2f}s).")

  return (None, True), res_audio


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
