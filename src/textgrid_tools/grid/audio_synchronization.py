from logging import Logger, getLogger
from typing import Optional

import numpy as np
from textgrid import IntervalTier, TextGrid

from textgrid_tools.globals import ExecutionResult
from textgrid_tools.helper import check_is_valid_grid, samples_to_s
from textgrid_tools.validation import InvalidGridError, ValidationError


class LastIntervalToShortError(ValidationError):
  def __init__(self, grid: TextGrid, audio: np.ndarray, sample_rate: int) -> None:
    super().__init__()
    self.grid = grid
    self.audio = audio
    self.sample_rate = sample_rate

  @classmethod
  def validate(cls, grid: TextGrid, audio: np.ndarray, sample_rate: int):
    if not can_set_end_to_audio_len(grid, audio, sample_rate):
      return cls(grid, audio, sample_rate)
    return None

  @property
  def default_message(self) -> str:
    return "Couldn't change maxTime because it would be <= than minTime of last interval!"


def sync_grid_to_audio(grid: TextGrid, audio: np.ndarray, sample_rate: int, logger: Optional[Logger]) -> ExecutionResult:
  if logger is None:
    logger = getLogger(__name__)

  if error := InvalidGridError.validate(grid):
    return error, False

  if error := LastIntervalToShortError.validate(grid, audio, sample_rate):
    return error, False

  changed_something = False

  old_min_time = grid.minTime
  set_minTime(grid, 0)

  if old_min_time != grid.minTime:
    changed_something = True
    logger.info(f"Adjusted start from {old_min_time} to 0.")

  old_max_time = grid.maxTime
  set_end_to_audio_len(grid, audio, sample_rate)

  if old_max_time != grid.maxTime:
    changed_something = True
    logger.info(f"Adjusted end from {old_max_time} to {grid.maxTime}.")

  return None, changed_something


def can_set_end_to_audio_len(grid: TextGrid, audio: np.ndarray, sample_rate: bool) -> bool:
  audio_duration_s = samples_to_s(audio.shape[0], sample_rate)
  #audio_duration_s = round(audio_duration_s, n_digits)
  return can_set_maxTime(grid, audio_duration_s)


def set_end_to_audio_len(grid: TextGrid, audio: np.ndarray, sample_rate: bool) -> None:
  assert can_set_end_to_audio_len(grid, audio, sample_rate)
  audio_duration_s = samples_to_s(audio.shape[0], sample_rate)
  #audio_duration_s = round(audio_duration_s, n_digits)

  set_maxTime(grid, audio_duration_s)


def can_set_maxTime(grid: TextGrid, max_time: float) -> bool:
  for tier in grid.tiers:
    if len(tier.intervals) > 0:
      if max_time <= tier.intervals[-1].minTime:
        return False
  return True


def set_maxTime(grid: TextGrid, max_time: float) -> None:
  assert check_is_valid_grid(grid)
  assert can_set_maxTime(grid, max_time)
  assert max_time > grid.minTime
  assert max_time > 0
  if grid.maxTime == max_time:
    return
  for tier in grid.tiers:
    set_maxTime_tier(tier, max_time)
  grid.maxTime = max_time
  assert check_is_valid_grid(grid)


def set_maxTime_tier(tier: IntervalTier, max_time: float) -> bool:
  assert tier.minTime < max_time
  changed_anything = False
  if len(tier.intervals) > 0:
    last_interval = tier.intervals[-1]
    assert last_interval.minTime < max_time
    if last_interval.maxTime != max_time:
      last_interval.maxTime = max_time
      changed_anything = True
  if tier.maxTime != max_time:
    tier.maxTime = max_time
    changed_anything = True
  return changed_anything


def set_minTime(grid: TextGrid, min_time: float) -> None:
  assert check_is_valid_grid(grid)
  assert min_time >= 0
  assert min_time < grid.maxTime
  if grid.minTime == min_time:
    return
  for tier in grid.tiers:
    if len(tier.intervals) > 0:
      assert tier.intervals[0].maxTime < min_time
      tier.intervals[0].minTime = min_time
    tier.minTime = min_time
  grid.minTime = min_time
  assert check_is_valid_grid(grid)
