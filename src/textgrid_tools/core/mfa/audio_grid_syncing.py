from logging import getLogger

import numpy as np
from audio_utils.audio import samples_to_s
from textgrid.textgrid import TextGrid
from textgrid_tools.core.mfa.helper import check_is_valid_grid


def can_sync_grid_to_audio(grid: TextGrid, audio: np.ndarray, sr: int, n_digits: int) -> bool:
  logger = getLogger(__name__)
  possible = can_set_end_to_audio_len(grid, audio, sr, n_digits)
  if not possible:
    logger.error(
      "Couldn't change maxTime because it would be <= than minTime for at least one last interval!")
    return False
  return True


def sync_grid_to_audio(grid: TextGrid, audio: np.ndarray, sr: int, n_digits: int) -> bool:
  assert can_sync_grid_to_audio(grid, audio, sr, n_digits)
  logger = getLogger(__name__)
  changed_something = False

  old_minTime = grid.minTime
  set_minTime(grid, 0)

  if old_minTime != grid.minTime:
    changed_something = True
    logger.info(f"Adjusted start from {old_minTime} to 0.")

  oldMaxTime = grid.maxTime
  set_end_to_audio_len(grid, audio, sr, n_digits)

  if oldMaxTime != grid.maxTime:
    changed_something = True
    logger.info(f"Adjusted end from {oldMaxTime} to {grid.maxTime}.")

  return changed_something


def can_set_end_to_audio_len(grid: TextGrid, audio: np.ndarray, sr: bool, n_digits: int) -> bool:
  audio_duration_s = samples_to_s(audio.shape[0], sr)
  audio_duration_s = round(audio_duration_s, n_digits)
  return can_set_maxTime(grid, audio_duration_s)


def set_end_to_audio_len(grid: TextGrid, audio: np.ndarray, sr: bool, n_digits: int) -> None:
  assert can_set_end_to_audio_len(grid, audio, sr, n_digits)
  audio_duration_s = samples_to_s(audio.shape[0], sr)
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
