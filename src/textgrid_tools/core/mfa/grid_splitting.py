from copy import deepcopy
from logging import getLogger
from typing import Iterable, List, Optional, Set, Tuple, cast

import numpy as np
from audio_utils.audio import s_to_samples
from textgrid.textgrid import IntervalTier, TextGrid
from textgrid_tools.core.mfa.audio_grid_syncing import set_end_to_audio_len
from textgrid_tools.core.mfa.helper import (
    check_timepoints_exist_on_all_tiers_as_boundaries,
    find_intervals_with_mark, get_intervals_from_timespan)
from tqdm import tqdm


def split_grid(grid: TextGrid, audio: np.ndarray, sr: int, reference_tier_name: str, split_markers: Set[str], n_digits: int) -> Tuple[bool, Optional[List[Tuple[TextGrid, np.ndarray]]]]:
  logger = getLogger(__name__)

  if s_to_samples(grid.maxTime, sr) != audio.shape[0]:
    logger.error(
      f"Audio length and grid length does not match ({audio.shape[0]} vs. {s_to_samples(grid.maxTime, sr)})")
    return False, None
    # audio_len = samples_to_s(audio.shape[0], sr)
    # set_maxTime(grid, audio_len)

  ref_tier: IntervalTier = grid.getFirst(reference_tier_name)
  if ref_tier is None:
    logger.exception("Tier not found!")
    raise Exception()

  split_intervals = list(find_intervals_with_mark(ref_tier, split_markers, include_empty=False))
  if len(split_intervals) == 0:
    return True, [(grid, audio)]
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

    all_tiers_share_timepoints = check_timepoints_exist_on_all_tiers_as_boundaries(
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
    assert end <= audio.shape[0]
    audio_part = range(start, end)
    grid_audio = audio[audio_part]

    # set ending correct
    success = set_end_to_audio_len(range_grid, grid_audio, sr, n_digits)
    if not success:
      logger.error("Couldn't set grid maxTime to audio len!")
      return False, None

    result.append((range_grid, grid_audio))
  durations = list(res_grid.maxTime for res_grid, _ in result)
  logger.info(f"# Files: {len(result)}")
  logger.info(f"Min duration: {min(durations):.2f}s")
  logger.info(f"Max duration: {max(durations):.2f}s")
  logger.info(f"Mean duration: {np.mean(durations):.2f}s")
  logger.info(f"Total duration: {sum(durations):.2f}s ({sum(durations)/60:.2f}min)")
  return True, result
