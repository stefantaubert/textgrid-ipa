from logging import getLogger

import numpy as np
from audio_utils.audio import samples_to_s
from textgrid.textgrid import TextGrid
from textgrid_tools.core.globals import ExecutionResult
from textgrid_tools.core.helper import check_is_valid_grid
from textgrid_tools.core.validation import InvalidGridError, ValidationError


class LastIntervalToShortError(ValidationError):
  def __init__(self, grid: TextGrid, audio: np.ndarray, sample_rate: int, n_digits: int) -> None:
    super().__init__()
    self.grid = grid
    self.audio = audio
    self.sample_rate = sample_rate
    self.n_digits = n_digits

  @classmethod
  def validate(cls, grid: TextGrid, audio: np.ndarray, sample_rate: int, n_digits: int):
    if not can_set_end_to_audio_len(grid, audio, sample_rate, n_digits):
      return cls(grid, audio, sample_rate, n_digits)
    return None

  @property
  def default_message(self) -> str:
    return "Couldn't change maxTime because it would be <= than minTime of last interval!"


def sync_grid_to_audio(grid: TextGrid, audio: np.ndarray, sample_rate: int, n_digits: int) -> ExecutionResult:
  if error := InvalidGridError.validate(grid):
    return error, False

  if error := LastIntervalToShortError.validate(grid, audio, sample_rate, n_digits):
    return error, False

  logger = getLogger(__name__)
  changed_something = False

  old_min_time = grid.minTime
  set_minTime(grid, 0)

  if old_min_time != grid.minTime:
    changed_something = True
    logger.info(f"Adjusted start from {old_min_time} to 0.")

  old_max_time = grid.maxTime
  set_end_to_audio_len(grid, audio, sample_rate, n_digits)

  if old_max_time != grid.maxTime:
    changed_something = True
    logger.info(f"Adjusted end from {old_max_time} to {grid.maxTime}.")

  return True, changed_something


def can_set_end_to_audio_len(grid: TextGrid, audio: np.ndarray, sample_rate: bool, n_digits: int) -> bool:
  audio_duration_s = samples_to_s(audio.shape[0], sample_rate)
  audio_duration_s = round(audio_duration_s, n_digits)
  return can_set_maxTime(grid, audio_duration_s)


def set_end_to_audio_len(grid: TextGrid, audio: np.ndarray, sample_rate: bool, n_digits: int) -> None:
  assert can_set_end_to_audio_len(grid, audio, sample_rate, n_digits)
  audio_duration_s = samples_to_s(audio.shape[0], sample_rate)
  audio_duration_s = round(audio_duration_s, n_digits)

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
    if len(tier.intervals) > 0:
      tier.intervals[-1].maxTime = max_time
    tier.maxTime = max_time
  grid.maxTime = max_time
  assert check_is_valid_grid(grid)


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
