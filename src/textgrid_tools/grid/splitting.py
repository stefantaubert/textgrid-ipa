from logging import Logger, getLogger
from typing import Iterable, List, Optional, Tuple, cast

import numpy as np
from textgrid.textgrid import Interval, IntervalTier, TextGrid

from textgrid_tools.cloning import copy_intervals
from textgrid_tools.globals import ExecutionResult
from textgrid_tools.grid.audio_synchronization import LastIntervalToShortError, set_end_to_audio_len
from textgrid_tools.helper import (get_boundary_timepoints_from_tier, get_intervals_on_tier,
                                   get_single_tier, interval_is_None_or_whitespace, s_to_samples)
from textgrid_tools.validation import (AudioAndGridLengthMismatchError, BoundaryError,
                                       InternalError, InvalidGridError,
                                       MultipleTiersWithThatNameError, NotExistingTierError)


def split_grid_on_intervals(grid: TextGrid, audio: Optional[np.ndarray], sample_rate: Optional[int], tier_name: str, include_empty_intervals: bool, logger: Optional[Logger]) -> Tuple[ExecutionResult, List[Tuple[TextGrid, Optional[np.ndarray]]]]:
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

  tier = get_single_tier(grid, tier_name)
  timepoints = get_boundary_timepoints_from_tier(tier)
  other_tiers = (
    grid_tier
    for grid_tier in grid.tiers
    if grid_tier != tier
  )

  if error := BoundaryError.validate(timepoints, other_tiers):
    return (error, False), None

  result: List[Tuple[TextGrid, Optional[np.ndarray]]] = []
  for interval in cast(Iterable[Interval], tier.intervals):
    if not include_empty_intervals and interval_is_None_or_whitespace(interval):
      continue

    extracted_grid = extract_grid(grid, interval)
    extracted_audio = None
    if audio is not None:
      extracted_audio = extract_audio(audio, sample_rate, interval)

      # after multiple removals in audio some difference occurs
      if error := LastIntervalToShortError.validate(extracted_grid, extracted_audio, sample_rate):
        internal_error = InternalError()
        return (internal_error, False), None

      set_end_to_audio_len(extracted_grid, extracted_audio, sample_rate)

    result.append((extracted_grid, extracted_audio))

  durations = list(res_grid.maxTime for res_grid, _ in result)
  logger.info(f"# Files: {len(result)}")
  logger.info(f"Min duration: {min(durations):.2f}s")
  logger.info(f"Max duration: {max(durations):.2f}s")
  logger.info(f"Mean duration: {np.mean(durations):.2f}s")
  logger.info(f"Total duration: {sum(durations):.2f}s ({sum(durations)/60:.2f}min)")
  return (None, True), result


def extract_grid(grid: TextGrid, interval: Interval) -> TextGrid:
  assert len(grid.tiers) > 0
  extracted_grid = TextGrid(
    name=grid.name,
    minTime=0,
    maxTime=0,
  )

  for grids_tier in cast(Iterable[IntervalTier], grid.tiers):
    grids_tier_intervals = get_intervals_on_tier(interval, grids_tier)
    grids_tier_intervals = list(copy_intervals(grids_tier_intervals, False))

    min_time_first_interval = grids_tier_intervals[0].minTime
    for grids_tier_interval in grids_tier_intervals:
      grids_tier_interval.minTime = grids_tier_interval.minTime - min_time_first_interval
      # grids_tier_interval.minTime = round(grids_tier_interval.minTime - min_time_first_interval, n_digits)
      grids_tier_interval.maxTime = grids_tier_interval.maxTime - min_time_first_interval
      # grids_tier_interval.maxTime = round(grids_tier_interval.maxTime - min_time_first_interval, n_digits)
    # assert no time between intervals
    max_time = grids_tier_intervals[-1].maxTime
    #max_time = round(grids_tier_intervals[-1].maxTime, n_digits)
    grids_tier_excerpt = IntervalTier(
      grids_tier.name,
      minTime=0,
      maxTime=max_time,
    )
    grids_tier_excerpt.intervals.extend(grids_tier_intervals)
    extracted_grid.tiers.append(grids_tier_excerpt)

  extracted_grid.maxTime = extracted_grid.tiers[0].maxTime

  return extracted_grid


def extract_audio(audio: np.ndarray, sample_rate: int, interval: Interval) -> np.ndarray:
  audio_start = s_to_samples(interval.minTime, sample_rate)
  audio_end = s_to_samples(interval.maxTime, sample_rate)
  assert audio_end <= audio.shape[0]
  audio_part = range(audio_start, audio_end)
  grid_audio = audio[audio_part]
  return grid_audio
