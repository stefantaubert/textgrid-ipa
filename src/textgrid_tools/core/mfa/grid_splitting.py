from copy import deepcopy
from logging import getLogger
from typing import Iterable, List, Set, Tuple, cast

import numpy as np
from audio_utils.audio import s_to_samples
from textgrid.textgrid import IntervalTier, TextGrid
from textgrid_tools.core.mfa.helper import (
    check_timepoints_exist_on_all_tiers, find_intervals_with_mark,
    get_intervals_from_timespan)
from tqdm import tqdm


def split_grid(grid: TextGrid, audio: np.ndarray, sr: int, reference_tier_name: str, split_markers: Set[str]) -> List[Tuple[TextGrid, np.ndarray]]:
  logger = getLogger(__name__)

  if s_to_samples(grid.maxTime, sr) != audio.shape[0]:
    logger.warning(
      f"Audio length and grid length does not match ({audio.shape[0]} vs. {s_to_samples(grid.maxTime, sr)})")
    # audio_len = samples_to_s(audio.shape[0], sr)
    # set_maxTime(grid, audio_len)

  ref_tier: IntervalTier = grid.getFirst(reference_tier_name)
  if ref_tier is None:
    logger.exception("Tier not found!")
    raise Exception()

  split_intervals = list(find_intervals_with_mark(ref_tier, split_markers))
  if len(split_intervals) == 0:
    return [(grid, audio)]
  target_intervals: List[Tuple[float, float]] = []
  if ref_tier.minTime < split_intervals[0].minTime:
    target_intervals.append((ref_tier.minTime, split_intervals[0].minTime))
  for i in range(1, len(split_intervals)):
    prev_interval = split_intervals[i - 1]
    curr_interval = split_intervals[i]
    start = prev_interval.maxTime
    end = curr_interval.minTime
    duration = end - start
    # eg if two split tiers are together
    if duration > 0:
      target_intervals.append((start, end))
  if split_intervals[-1].maxTime < ref_tier.maxTime:
    target_intervals.append((split_intervals[-1].maxTime, ref_tier.maxTime))
  result = []

  for minTime, maxTime in tqdm(target_intervals):
    range_grid = TextGrid(
      name=None,
      minTime=0,
      maxTime=0,
    )

    all_tiers_share_timepoints = check_timepoints_exist_on_all_tiers(
      timepoints=[minTime, maxTime], tiers=grid.tiers)
    if not all_tiers_share_timepoints:
      logger.warning(
        f"Skipping interval [{minTime}, {maxTime}] because it does not exist on all tiers.")
      continue

    for tier in cast(Iterable[IntervalTier], grid.tiers):
      intervals_in_range = list(get_intervals_from_timespan(
        tier, minTime, maxTime))
      intervals_in_range = deepcopy(intervals_in_range)
      assert len(intervals_in_range) > 0
      assert intervals_in_range[0].minTime == minTime
      assert intervals_in_range[-1].maxTime == maxTime

      minTime_first_interval = intervals_in_range[0].minTime
      for interval in intervals_in_range:
        interval.minTime -= minTime_first_interval
        interval.maxTime -= minTime_first_interval
      # assert no time between intervals
      duration = intervals_in_range[-1].maxTime
      new_tier = IntervalTier(
        tier.name,
        minTime=0,
        maxTime=duration,
      )
      for interval in intervals_in_range:
        new_tier.intervals.append(interval)
      range_grid.tiers.append(new_tier)

    if len(range_grid.tiers) > 0:
      range_grid.maxTime = range_grid.tiers[0].maxTime

    start = s_to_samples(minTime, sr)
    end = s_to_samples(maxTime, sr)
    if end > audio.shape[0]:
      logger.warning(f"Ending of audio overreached by {end - audio.shape[0]} sample(s)!")
      end = audio.shape[0]
      assert end >= start
    audio_part = range(start, end)
    grid_audio = audio[audio_part]
    result.append((range_grid, grid_audio))

  return result
