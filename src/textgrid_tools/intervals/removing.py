import math
from logging import Logger, getLogger
from typing import Generator, Iterable, List, Literal, Optional, Set, Tuple, cast

import numpy as np
from ordered_set import OrderedSet
from textgrid.textgrid import Interval, IntervalTier, TextGrid

from textgrid_tools.globals import ExecutionResult
from textgrid_tools.grid.audio_synchronization import LastIntervalToShortError, set_end_to_audio_len
from textgrid_tools.helper import (check_is_valid_grid,
                                   check_timepoints_exist_on_all_tiers_as_boundaries,
                                   get_intervals_from_timespans_match, get_single_tier,
                                   s_to_samples)
from textgrid_tools.intervals.boundary_fixing import fix_timepoint
from textgrid_tools.validation import (AudioAndGridLengthMismatchError, InternalError,
                                       InvalidGridError, MultipleTiersWithThatNameError,
                                       NotExistingTierError)


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
  success = remove_intervals_from_tiers(intervals_to_remove, grid.tiers, logger)
  if not success:
    internal_error = InternalError()
    return (internal_error, False), None

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


def check_contains_consecutives(min_max_times: Set[Tuple[float, float]]) -> bool:
  min_times = {time for time, _ in min_max_times}
  max_times = {time for _, time in min_max_times}
  for min_time, max_time in min_max_times:
    if min_time in max_times:
      return True
    if max_time in min_times:
      return True
  return False


def merge_consecutives(min_max_times: OrderedSet[Tuple[float, float]]) -> OrderedSet[Tuple[float, float]]:
  if len(min_max_times) == 0:
    return OrderedSet()

  if len(min_max_times) == 1:
    return OrderedSet([min_max_times[0]])

  result = OrderedSet()
  current_range = [min_max_times[0][0]]
  max_time = None
  for i, (min_time, max_time) in enumerate(min_max_times[1:], start=1):
    last_min_time, last_max_time = min_max_times[i - 1]
    if min_time == last_max_time:
      continue
    else:
      current_range.append(last_max_time)
      result.add(tuple(current_range))
      current_range.clear()
      current_range.append(min_time)
  if len(current_range) == 1:
    assert max_time is not None
    current_range.append(max_time)
    result.add(tuple(current_range))
  return result


def get_sync_times(min_max_times: Set[Tuple[float, float]], max_time: float) -> OrderedSet[float]:
  assert not check_contains_consecutives(min_max_times)
  times = list(min_max_times)
  times.sort(key=lambda x: x[0])
  currently_removed_difference = 0
  result = OrderedSet()
  if len(min_max_times) == 0:
    return OrderedSet()
  current_max_time: float = None
  for current_min_time, current_max_time in min_max_times:
    assert current_min_time < current_max_time
    timepoint = current_min_time - currently_removed_difference
    result.add(timepoint)
    difference = current_max_time - current_min_time
    currently_removed_difference += difference
  assert current_max_time is not None
  last_interval_is_removed = current_max_time == max_time
  if not last_interval_is_removed:
    # Note: through rounding errors its better to check if last interval is removed instead of adding the max_time to set (which will be ignored in that case since it already exists)
    new_max_time = max_time - currently_removed_difference
    result.add(new_max_time)
  return result


def remove_intervals_from_tiers(intervals_to_remove: List[Interval], tiers: List[IntervalTier], logger: Logger) -> bool:
  if len(tiers) == 0:
    return True

  min_max_times = OrderedSet([
    (interval.minTime, interval.maxTime)
    for interval in intervals_to_remove
  ])
  min_max_times = merge_consecutives(min_max_times)

  times_across_all_tiers = OrderedSet([
    a_or_b
    for ab in min_max_times
    for a_or_b in ab
  ])

  if not check_timepoints_exist_on_all_tiers_as_boundaries(times_across_all_tiers, tiers):
    logger.debug("Boundaries do not exist on all tiers!")
    return False

  tiers_max_time = tiers[0].maxTime
  for tier in tiers[1:]:
    assert tier.maxTime == tiers_max_time

  sync_times = get_sync_times(min_max_times, tiers_max_time)

  for tier in tiers:
    assert len(tier.intervals) > 0
    matching_intervals = get_intervals_from_timespans_match(tier, min_max_times)
    old_min_time = tier.intervals[0].minTime
    move_first_interval = False
    if tier.intervals[0] in matching_intervals:
      move_first_interval = True
    for interval in matching_intervals:
      tier.intervals.remove(interval)

    all_intervals_were_removed = len(tier.intervals) == 0
    if all_intervals_were_removed:
      continue

    if move_first_interval:
      move_interval(tier.intervals[0], old_min_time)

    set_times_consecutively_intervals(tier.intervals)
    tier.maxTime = tier.intervals[-1].maxTime
    for sync_time in sync_times:
      success, changes = fix_timepoint(sync_time, tier, math.inf, logger)
      if not success:
        return False

  all_tiers_share_sync_times = check_timepoints_exist_on_all_tiers_as_boundaries(
    sync_times, tiers)
  assert all_tiers_share_sync_times
  return True


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
