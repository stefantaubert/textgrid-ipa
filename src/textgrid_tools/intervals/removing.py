import math
from logging import Logger, getLogger
from typing import Generator, Iterable, List, Literal, Optional, Set, Tuple, cast

import numpy as np
from textgrid.textgrid import Interval, IntervalTier, TextGrid
from tqdm import tqdm

from textgrid_tools.globals import ExecutionResult
from textgrid_tools.grid.audio_synchronization import (LastIntervalToShortError,
                                                       set_end_to_audio_len, set_maxTime_tier)
from textgrid_tools.helper import (check_is_valid_grid,
                                   check_timepoints_exist_on_all_tiers_as_boundaries,
                                   get_boundary_timepoints_from_intervals,
                                   get_boundary_timepoints_from_tier, get_intervals_on_tier,
                                   get_single_tier, s_to_samples)
from textgrid_tools.intervals.boundary_fixing import fix_timepoint
from textgrid_tools.validation import (AudioAndGridLengthMismatchError, BoundaryError,
                                       InternalError, InvalidGridError,
                                       MultipleTiersWithThatNameError, NotExistingTierError)


def remove_intervals(grid: TextGrid, audio: Optional[np.ndarray], sample_rate: Optional[int], tier_name: str, remove_marks: Set[str], mode: Literal["all", "start", "end", "both"], logger: Optional[Logger]) -> Tuple[ExecutionResult, Optional[np.ndarray]]:
  if logger is None:
    logger = getLogger(__name__)

  if error := InvalidGridError.validate(grid):
    return (error, False), None

  if error := NotExistingTierError.validate(grid, tier_name):
    return (error, False), None

  if error := MultipleTiersWithThatNameError.validate(grid, tier_name):
    return (error, False), None

  if audio is not None:
    assert sample_rate is not None
    if error := AudioAndGridLengthMismatchError.validate(grid, audio, sample_rate):
      return (error, False), None

  if logger is None:
    logger = getLogger(__name__)

  ref_tier = get_single_tier(grid, tier_name)

  intervals_to_remove = list(get_intervals_mode(ref_tier, remove_marks, mode))
  timepoints = get_boundary_timepoints_from_intervals(intervals_to_remove)

  if error := BoundaryError.validate(timepoints, grid.tiers):
    return (error, False), None

  for interval in intervals_to_remove:
    for interval_on_tier in get_intervals_on_tier(interval, ref_tier):
      ref_tier.removeInterval(interval_on_tier)
  if len(ref_tier.intervals) > 0:
    move_interval(ref_tier.intervals[0], 0)
    set_times_consecutively_tier(ref_tier)

  sync_timepoints = get_boundary_timepoints_from_tier(ref_tier)

  for tier in cast(Iterable[IntervalTier], tqdm(grid.tiers)):
    if tier == ref_tier:
      continue
    for interval in intervals_to_remove:
      for interval_on_tier in get_intervals_on_tier(interval, tier):
        tier.removeInterval(interval_on_tier)
    if len(tier.intervals) > 0:
      move_interval(tier.intervals[0], 0)
      set_times_consecutively_tier(tier)
      if not ref_tier.maxTime > tier.minTime:
        raise InternalError()
      set_maxTime_tier(tier, ref_tier.maxTime)

    for timepoint in sync_timepoints:
      fix_timepoint(timepoint, tier, math.inf, logger)

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
    for interval in reversed(intervals_to_remove):
      start = s_to_samples(interval.minTime, sample_rate)
      end = s_to_samples(interval.maxTime, sample_rate)
      assert end <= audio.shape[0]
      r = range(start, end)
      remove_range.extend(r)
    res_audio = np.delete(audio, remove_range, axis=0)

    # after multiple removals in audio some difference occurs
    if error := LastIntervalToShortError.validate(grid, res_audio, sample_rate):
      internal_error = InternalError()
      return (internal_error, False), None

    set_end_to_audio_len(grid, res_audio, sample_rate)

  removed_duration = sum(interval.duration() for interval in intervals_to_remove)
  logger.info(f"Removed {len(intervals_to_remove)} intervals ({removed_duration:.2f}s).")

  return (None, True), res_audio


def set_times_consecutively_tier(tier: IntervalTier):
  set_times_consecutively_intervals(tier.intervals)

  if len(tier.intervals) > 0:
    if cast(Interval, tier.intervals[0]).minTime != tier.minTime:
      tier.minTime = cast(Interval, tier.intervals[0]).minTime

    if cast(Interval, tier.intervals[-1]).maxTime != tier.maxTime:
      tier.maxTime = cast(Interval, tier.intervals[-1]).maxTime


def set_times_consecutively_intervals(intervals: List[Interval]):
  # could be the case that imprecisions are induced e.g. 0.95000000000000002
  for i in range(1, len(intervals)):
    prev_interval = cast(Interval, intervals[i - 1])
    current_interval = cast(Interval, intervals[i])
    gap_exists = current_interval.minTime != prev_interval.maxTime
    if gap_exists:
      assert prev_interval.maxTime < current_interval.minTime
      move_interval(current_interval, prev_interval.maxTime)


def move_interval(interval: Interval, new_minTime: float) -> None:
  if interval.minTime == new_minTime:
    return
  duration = interval.duration()
  interval.minTime = new_minTime
  interval.maxTime = interval.minTime + duration
  # set_precision_interval(interval, n_digits)


def get_intervals_start(tier: List[Interval], marks: Set[str]) -> Generator[Interval, None, None]:
  for interval in tier.intervals:
    if interval.mark in marks:
      yield interval
      continue
    break


def get_intervals_end(intervals: List[Interval], marks: Set[str]) -> Generator[Interval, None, None]:
  for interval in reversed(intervals):
    if interval.mark in marks:
      yield interval
      continue
    break


def get_intervals_both(intervals: List[Interval], marks: Set[str]) -> Generator[Interval, None, None]:
  start_intervals = list(get_intervals_start(intervals, marks))
  rest_intervals = intervals[len(start_intervals):]
  end_intervals = list(get_intervals_end(rest_intervals, marks))
  yield from start_intervals
  yield from end_intervals


def get_intervals_all(tier: Iterable[Interval], marks: Set[str]) -> Generator[Interval, None, None]:
  for interval in cast(Iterable[Interval], tier.intervals):
    if interval.mark in marks:
      yield interval


def get_intervals_mode(tier: IntervalTier, marks: Set[str], mode: Literal["all", "start", "end", "both"]) -> Generator[Interval, None, None]:
  if mode == "all":
    yield from get_intervals_all(tier, marks)
  elif mode == "start":
    yield from get_intervals_start(tier, marks)
  elif mode == "end":
    yield from get_intervals_end(tier, marks)
  elif mode == "both":
    yield from get_intervals_both(tier, marks)
  else:
    assert False
