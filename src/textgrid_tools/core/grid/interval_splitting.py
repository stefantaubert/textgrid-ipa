from copy import deepcopy
from logging import getLogger
from typing import Iterable, List, Tuple, cast

import numpy as np
from audio_utils.audio import s_to_samples
from textgrid.textgrid import Interval, IntervalTier, TextGrid
from textgrid_tools.core.mfa.grid_audio_synchronization import (
    can_set_end_to_audio_len, set_end_to_audio_len)
from textgrid_tools.core.mfa.helper import (
    check_is_valid_grid, check_timepoints_exist_on_all_tiers_as_boundaries,
    get_boundary_timepoints_from_tier, get_first_tier, get_intervals_on_tier,
    interval_is_None_or_whitespace, tier_exists)


def can_split_grid_on_intervals(grid: TextGrid, audio: np.ndarray, sample_rate: int, tier_name: str) -> bool:
  logger = getLogger(__name__)

  if not check_is_valid_grid(grid):
    logger.error("Grid is invalid!")
    return False

  if not tier_exists(grid, tier_name):
    logger.error(f"Tier \"{tier_name}\" not found!")
    return False

  if s_to_samples(grid.maxTime, sample_rate) != audio.shape[0]:
    logger.error(
      f"Audio length and grid length does not match ({audio.shape[0]} vs. {s_to_samples(grid.maxTime, sample_rate)})")
    return False

  ref_tier = get_first_tier(grid, tier_name)
  timepoints = get_boundary_timepoints_from_tier(ref_tier)

  all_tiers_share_timepoints = check_timepoints_exist_on_all_tiers_as_boundaries(
    timepoints, grid.tiers)
  if not all_tiers_share_timepoints:
    logger.error(f"Not all tiers share the same interval boundaries as tier \"{tier_name}\"!")
    return False

  return True


def split_grid_on_intervals(grid: TextGrid, audio: np.ndarray, sample_rate: int, tier_name: str, include_empty_intervals: bool, n_digits: int) -> List[Tuple[TextGrid, np.ndarray]]:
  assert can_split_grid_on_intervals(grid, audio, sample_rate, tier_name)
  result: List[Tuple[TextGrid, np.ndarray]] = []

  tier = get_first_tier(grid, tier_name)
  for interval in cast(Iterable[Interval], tier.intervals):
    if not include_empty_intervals and interval_is_None_or_whitespace(interval):
      continue
    extracted_grid, extracted_audio = extract_grid_and_audio(
      grid, interval, audio, sample_rate, n_digits)
    result.append((extracted_grid, extracted_audio))

  durations = list(res_grid.maxTime for res_grid, _ in result)

  logger = getLogger(__name__)
  logger.info(f"# Files: {len(result)}")
  logger.info(f"Min duration: {min(durations):.2f}s")
  logger.info(f"Max duration: {max(durations):.2f}s")
  logger.info(f"Mean duration: {np.mean(durations):.2f}s")
  logger.info(f"Total duration: {sum(durations):.2f}s ({sum(durations)/60:.2f}min)")
  return result


def extract_grid_and_audio(grid: TextGrid, interval: Interval, audio: np.ndarray, sample_rate: int, n_digits: int) -> Tuple[TextGrid, np.ndarray]:
  extracted_grid = TextGrid(
    name=grid.name,
    minTime=0,
    maxTime=0,
  )

  for grids_tier in cast(Iterable[IntervalTier], grid.tiers):
    grids_tier_intervals = get_intervals_on_tier(interval, grids_tier)
    grids_tier_intervals = deepcopy(grids_tier_intervals)

    minTime_first_interval = grids_tier_intervals[0].minTime
    for grids_tier_interval in grids_tier_intervals:
      grids_tier_interval.minTime -= minTime_first_interval
      grids_tier_interval.maxTime -= minTime_first_interval
    # assert no time between intervals
    duration = grids_tier_intervals[-1].maxTime
    grids_tier_excerpt = IntervalTier(
      grids_tier.name,
      minTime=0,
      maxTime=duration,
    )
    for grids_tier_interval in grids_tier_intervals:
      grids_tier_excerpt.intervals.append(grids_tier_interval)
    extracted_grid.tiers.append(grids_tier_excerpt)

  if len(extracted_grid.tiers) > 0:
    extracted_grid.maxTime = extracted_grid.tiers[0].maxTime

  extracted_audio = get_audio_from_interval(audio, sample_rate, interval)

  # set ending correct
  success = can_set_end_to_audio_len(extracted_grid, extracted_audio, sample_rate, n_digits)
  if not success:
    logger = getLogger(__name__)
    logger.error("Couldn't set grid maxTime to audio len!")
    raise Exception()

  set_end_to_audio_len(extracted_grid, extracted_audio, sample_rate, n_digits)
  return extracted_grid, extracted_audio


def get_audio_from_interval(audio: np.ndarray, sample_rate: int, interval: Interval) -> np.ndarray:
  audio_start = s_to_samples(interval.minTime, sample_rate)
  audio_end = s_to_samples(interval.maxTime, sample_rate)
  assert audio_end <= audio.shape[0]
  audio_part = range(audio_start, audio_end)
  grid_audio = audio[audio_part]
  return grid_audio
