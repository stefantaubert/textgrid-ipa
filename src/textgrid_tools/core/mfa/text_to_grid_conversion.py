from logging import getLogger
from typing import Optional, Tuple

import numpy as np
from audio_utils.audio import samples_to_s
from textgrid.textgrid import Interval, IntervalTier, TextGrid
from textgrid_tools.core.mfa.helper import check_is_valid_grid
from textgrid_tools.core.mfa.string_format import StringFormat, get_symbols


def can_convert_texts_to_grid(tier_out: str, characters_per_second: float) -> bool:
  logger = getLogger(__name__)
  if len(tier_out) == 0:
    logger.error("Please specify an output name!")
    return False

  if characters_per_second <= 0:
    logger.error("characters_per_second need to be > 0!")
    return False
  return True


def can_convert_text_to_grid(audio: Optional[np.ndarray], sr: Optional[int], start: Optional[float], end: Optional[float]) -> bool:
  logger = getLogger(__name__)

  if start is not None:
    if not start >= 0:
      logger.error("Start needs to be >= 0!")
      return False

  if end is not None:
    if not end > 0:
      logger.error("End needs to be > 0!")
      return False

  if audio is not None:
    assert sr is not None
    duration_s = samples_to_s(audio.shape[0], sr)
    if start is not None and not start < duration_s:
      logger.error("Start needs to be smaller than audio duration!")
      return False
    if end is not None and not end <= duration_s:
      logger.error("End needs to be smaller or equal than audio duration!")
      return False
    if start is not None and end is not None:
      if not start < end:
        logger.error("Start needs to be smaller than end!")
        return False

  return True


def get_character_count(text: str, string_format: StringFormat) -> int:
  if string_format == StringFormat.TEXT:
    total_characters = len(text)
    return total_characters

  if string_format == StringFormat.SYMBOLS:
    words = string_format.get_words(text)
    words_symbols = (get_symbols(word) for word in words)
    count_space = max(0, len(words) - 1)
    total_characters = sum(1 for word in words_symbols for symbol in word) + count_space
    return total_characters
  assert False


def can_parse_float(float_str: str) -> bool:
  try:
    float(float_str)
    return True
  except ValueError:
    return False
  assert False


def parse_meta_content(meta_content: str) -> Tuple[Optional[float], Optional[float]]:
  assert can_parse_meta_content(meta_content)
  lines = meta_content.split("\n")
  start = None
  end = None
  if len(lines) >= 1:
    start = float(lines[0])
  if len(lines) >= 2:
    end = float(lines[1])
  return start, end


def can_parse_meta_content(meta_content: str) -> bool:
  lines = meta_content.split("\n")
  if len(lines) >= 1:
    start_line = lines[0]
    if not can_parse_float(start_line):
      return False
  if len(lines) >= 2:
    end_line = lines[1]
    if not can_parse_float(end_line):
      return False
  return True


def convert_text_to_grid(text: str, audio: Optional[np.ndarray], sr: Optional[int], grid_name_out: Optional[str], tier_out: str, characters_per_second: float, n_digits: int, start: Optional[float], end: Optional[float], string_format: StringFormat) -> TextGrid:
  assert can_convert_texts_to_grid(tier_out, characters_per_second)
  logger = getLogger(__name__)
  duration_s: float = None
  if audio is not None:
    assert sr is not None
    duration_s = samples_to_s(audio.shape[0], sr)
    logger.info(f"Total grid duration is {duration_s}.")
  else:
    total_characters = get_character_count(text, string_format)
    duration_s = total_characters / characters_per_second
    logger.info(f"Estimated grid duration to {duration_s}.")

  if duration_s == 0:
    duration_s = 1
    logger.info("Adjusted grid duration to one second since it would be zero otherwise.")

  minTime_text_interval = 0
  maxTime_text_interval = duration_s
  if start is not None:
    minTime_text_interval = round(start, n_digits)
    logger.info(f"Set start of grid to {start}.")
  if end is not None:
    maxTime_text_interval = round(end, n_digits)
    logger.info(f"Set end of grid to {end}.")

  if maxTime_text_interval > duration_s:
    logger.info(
      f"End was longer than the audio, therefore adjusting it from {maxTime_text_interval} to {duration_s}.")
    maxTime_text_interval = duration_s

  minTime = 0
  maxTime = duration_s

  grid = TextGrid(
    minTime=minTime,
    maxTime=maxTime,
    name=grid_name_out,
    strict=True,
  )

  tier = IntervalTier(
    name=tier_out,
    minTime=minTime,
    maxTime=maxTime,
  )

  if minTime < minTime_text_interval:
    start_interval = Interval(
      minTime=0,
      maxTime=minTime_text_interval,
      mark="",
    )
    tier.addInterval(start_interval)

  interval = Interval(
    minTime=minTime_text_interval,
    maxTime=maxTime_text_interval,
    mark=text,
  )
  tier.addInterval(interval)

  if maxTime_text_interval < maxTime:
    start_interval = Interval(
      minTime=maxTime_text_interval,
      maxTime=maxTime,
      mark="",
    )
    tier.addInterval(start_interval)

  grid.append(tier)

  assert check_is_valid_grid(grid)
  return grid
