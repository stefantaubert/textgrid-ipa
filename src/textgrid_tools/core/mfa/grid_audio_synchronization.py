from logging import getLogger

import numpy as np
from audio_utils.audio import samples_to_s
from textgrid.textgrid import TextGrid
from textgrid_tools.core.globals import ExecutionResult
from textgrid_tools.core.mfa.helper import check_is_valid_grid
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

  old_minTime = grid.minTime
  set_minTime(grid, 0)

  if old_minTime != grid.minTime:
    changed_something = True
    logger.info(f"Adjusted start from {old_minTime} to 0.")

  oldMaxTime = grid.maxTime
  set_end_to_audio_len(grid, audio, sample_rate, n_digits)

  if oldMaxTime != grid.maxTime:
    changed_something = True
    logger.info(f"Adjusted end from {oldMaxTime} to {grid.maxTime}.")

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


def can_set_maxTime(grid: TextGrid, maxTime: float) -> bool:
  for tier in grid.tiers:
    if len(tier.intervals) > 0:
      if maxTime <= tier.intervals[-1].minTime:
        return False
  return True


def set_maxTime(grid: TextGrid, maxTime: float) -> None:
  assert check_is_valid_grid(grid)
  assert can_set_maxTime(grid, maxTime)
  assert maxTime > grid.minTime
  assert maxTime > 0
  if grid.maxTime == maxTime:
    return
  for tier in grid.tiers:
    if len(tier.intervals) > 0:
      tier.intervals[-1].maxTime = maxTime
    tier.maxTime = maxTime
  grid.maxTime = maxTime
  assert check_is_valid_grid(grid)


def set_minTime(grid: TextGrid, minTime: float) -> None:
  assert check_is_valid_grid(grid)
  assert minTime >= 0
  assert minTime < grid.maxTime
  if grid.minTime == minTime:
    return
  for tier in grid.tiers:
    if len(tier.intervals) > 0:
      assert tier.intervals[0].maxTime < minTime
      tier.intervals[0].minTime = minTime
    tier.minTime = minTime
  grid.minTime = minTime
  assert check_is_valid_grid(grid)
