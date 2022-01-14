from logging import getLogger
from math import ceil
from typing import Optional, Tuple

import numpy as np
from audio_utils.audio import s_to_samples, samples_to_s
from text_utils import StringFormat
from textgrid.textgrid import Interval, IntervalTier, TextGrid
from textgrid_tools.core.globals import ExecutionResult
from textgrid_tools.core.helper import can_parse_float, check_is_valid_grid
from textgrid_tools.core.validation import (InvalidStringFormatIntervalError,
                                            InvalidTierNameError,
                                            ValidationError)


class InvalidReadingSpeedError(ValidationError):
  def __init__(self, speed: float) -> None:
    super().__init__()
    self.speed = speed

  @classmethod
  def validate(cls, speed: float):
    if not speed > 0:
      return cls(speed)
    return None

  @property
  def default_message(self) -> str:
    return f"Speed needs to be greater than zero but was \"{self.speed}\"!"


class StartNotSmallerThanEndError(ValidationError):
  def __init__(self, start: float, end: float) -> None:
    super().__init__()
    self.start = start
    self.end = end

  @classmethod
  def validate(cls, start: float, end: float):
    if not start < end:
      return cls(start, end)
    return None

  @property
  def default_message(self) -> str:
    return f"Start (\"{self.start}\") needs to be smaller than end (\"{self.end}\")!"


class StartTooSmallError(ValidationError):
  def __init__(self, start: float) -> None:
    super().__init__()
    self.start = start

  @classmethod
  def validate(cls, start: float):
    if not start >= 0:
      return cls(start)
    return None

  @property
  def default_message(self) -> str:
    return f"Start needs to be greater than or equal to zero but was \"{self.start}\"!"


class StartTooBigError(ValidationError):
  def __init__(self, start: float, audio_duration: float) -> None:
    super().__init__()
    self.start = start
    self.audio_duration = audio_duration

  @classmethod
  def validate(cls, start: float, audio_duration: float):
    if not start < audio_duration:
      return cls(start, audio_duration)
    return None

  @property
  def default_message(self) -> str:
    return f"Start (\"{self.start}\") needs to be smaller than the audio duration (\"{self.audio_duration}\")!"


class EndTooBigError(ValidationError):
  def __init__(self, end: float, audio_duration: float) -> None:
    super().__init__()
    self.end = end
    self.audio_duration = audio_duration

  @classmethod
  def validate(cls, end: float, audio_duration: float):
    if not end < audio_duration:
      return cls(end, audio_duration)
    return None

  @property
  def default_message(self) -> str:
    return f"End (\"{self.end}\") needs to be smaller than or equal to the audio duration (\"{self.audio_duration}\")!"


class EndTooSmallError(ValidationError):
  def __init__(self, end: float) -> None:
    super().__init__()
    self.end = end

  @classmethod
  def validate(cls, end: float):
    if not end > 0:
      return cls(end)
    return None

  @property
  def default_message(self) -> str:
    return f"End needs to be greater than zero but was \"{self.end}\"!"


class InvalidMetaFormatError(ValidationError):
  def __init__(self, meta: str) -> None:
    super().__init__()
    self.meta = meta

  @classmethod
  def validate(cls, meta: str):
    can_parse_meta = can_parse_meta_content(meta)
    if not can_parse_meta:
      return cls(meta)
    return None

  @property
  def default_message(self) -> str:
    return f"Meta content could not be parsed:\n\n```\n{self.meta}\n```!"


class TextEmptyError(ValidationError):
  def __init__(self, text: str) -> None:
    super().__init__()
    self.text = text

  @classmethod
  def validate(cls, text: str):
    if text.strip() == "":
      return cls(text)
    return None

  @property
  def default_message(self) -> str:
    return f"Text content must not be empty:\n\n```\n{self.text}\n```!"




def create_grid_from_text(text: str, text_string_format: StringFormat, meta: Optional[str], audio: Optional[np.ndarray], sample_rate: Optional[int], grid_name: Optional[str], tier_name: str, characters_per_second: float, n_digits: int) -> Tuple[ExecutionResult, Optional[TextGrid]]:
  assert n_digits >= 0
  logger = getLogger(__name__)

  if audio is not None:
    assert sample_rate is not None

  if error := TextEmptyError.validate(text):
    return error, False

  if error := InvalidStringFormatIntervalError.validate(text, text_string_format):
    return error, False

  if error := InvalidTierNameError.validate(tier_name):
    return error, False

  if error := InvalidReadingSpeedError.validate(characters_per_second):
    return error, False

  if meta is not None:
    if error := InvalidMetaFormatError.validate(meta):
      return error, False

    start, end = parse_meta_content(meta)

    # if start is not None and sample_rate is not None:
    #   new_start = get_closest_sample_rate_s(start, sample_rate)
    #   if start != new_start:
    #     logger.debug(f"Adjusted start to: {new_start}")
    #     start = new_start

    # if end is not None and sample_rate is not None:
    #   new_end = get_closest_sample_rate_s(end, sample_rate)
    #   if end != new_end:
    #     logger.debug(f"Adjusted start to: {new_end}")
    #     end = new_end

    if start is not None and (error := StartTooSmallError.validate(start)):
      return error, False

    if end is not None and (error := EndTooSmallError.validate(end)):
      return error, False

    if start is not None and end is not None:
      if error := StartNotSmallerThanEndError.validate(start, end):
        return error, False

    if audio is not None:
      duration_s = samples_to_s(audio.shape[0], sample_rate)

      if start is not None and (error := StartTooBigError.validate(start, duration_s)):
        return error, False

      if end is not None and (error := EndTooBigError.validate(end, duration_s)):
        return error, False
  else:
    start = None
    end = None

  text_symbols = text_string_format.convert_string_to_symbols(text)
  assert len(text_symbols) > 0

  duration_s: float = None

  if audio is None:
    duration_s = len(text_symbols) / characters_per_second
    logger.debug(f"Estimated grid duration to {duration_s}s.")
  else:
    duration_s = samples_to_s(audio.shape[0], sample_rate)
    logger.debug(f"Total grid duration is {duration_s}s.")

  min_time = 0
  max_time = round(duration_s, n_digits)

  min_time_text_interval = min_time
  max_time_text_interval = max_time

  if start is not None:
    min_time_text_interval = round(start, n_digits)
    logger.info(f"Set start of grid to {start}.")

  if end is not None:
    max_time_text_interval = round(end, n_digits)
    logger.info(f"Set end of grid to {end}.")

  mark = text_string_format.convert_symbols_to_string(text_symbols)
  result = get_grid(grid_name, tier_name, min_time, min_time_text_interval,
                    mark, max_time_text_interval, max_time)
  return (None, True), result


def get_grid(grid_name: str, tier_name: str, min_time: float, min_time_text_interval: float, mark: str, max_time_text_interval: float, max_time: float,) -> TextGrid:
  grid = TextGrid(
    minTime=min_time,
    maxTime=max_time,
    name=grid_name,
    strict=True,
  )

  tier = IntervalTier(
    name=tier_name,
    minTime=grid.minTime,
    maxTime=grid.maxTime,
  )

  if min_time < min_time_text_interval:
    start_interval = Interval(
      minTime=min_time,
      maxTime=min_time_text_interval,
      mark="",
    )
    tier.addInterval(start_interval)

  interval = Interval(
    minTime=min_time_text_interval,
    maxTime=max_time_text_interval,
    mark=mark,
  )
  tier.addInterval(interval)

  if max_time_text_interval < max_time:
    end_interval = Interval(
      minTime=max_time_text_interval,
      maxTime=max_time,
      mark="",
    )
    tier.addInterval(end_interval)

  grid.append(tier)

  assert check_is_valid_grid(grid)
  return grid


def parse_meta_content(meta_content: str) -> Tuple[Optional[float], Optional[float]]:
  assert can_parse_meta_content(meta_content)
  lines = meta_content.split("\n")
  start = None
  end = None
  if len(lines) >= 1:
    start = float(lines[0])
  if len(lines) >= 2:
    end = float(lines[1])

  logger = getLogger(__name__)
  logger.debug(f"Parsed meta content: [{start}, {end}].")
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
