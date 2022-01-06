from typing import Iterable, Set, cast

import numpy as np
from audio_utils.audio import s_to_samples
from ordered_set import OrderedSet
from text_utils.string_format import StringFormat
from textgrid.textgrid import Interval, IntervalTier, TextGrid
from textgrid_tools.core.mfa.helper import (
    check_is_valid_grid, check_timepoints_exist_on_all_tiers_as_boundaries,
    get_interval_readable, interval_is_None_or_empty, tier_exists)
from textgrid_tools.core.mfa.interval_format import IntervalFormat


class ValidationError():
  # pylint: disable=no-self-use
  @property
  def default_message(self) -> str:
    return ""



class NoTiersDefinedError(ValidationError):
  @classmethod
  def validate(cls, tiers: Set[str]):
    if len(tiers) == 0:
      return cls()
    return None

  @property
  def default_message(self) -> str:
    return "No tiers were defined!"

class NotExistingTierError(ValidationError):
  def __init__(self, grid: TextGrid, tier_name: str) -> None:
    super().__init__()
    self.grid = grid
    self.tier_name = tier_name

  @classmethod
  def validate(cls, grid: TextGrid, tier_name: str):
    if not tier_exists(grid, tier_name):
      return cls(grid, tier_name)
    return None

  @property
  def default_message(self) -> str:
    return f"Tier \"{self.tier_name}\" does not exist!"


class ExistingTierError(ValidationError):
  def __init__(self, grid: TextGrid, tier_name: str) -> None:
    super().__init__()
    self.grid = grid
    self.tier_name = tier_name

  @classmethod
  def validate(cls, grid: TextGrid, tier_name: str):
    """returns an error if the tier exist"""
    if tier_exists(grid, tier_name):
      return cls(grid, tier_name)
    return None

  @property
  def default_message(self) -> str:
    return f"Tier \"{self.tier_name}\" already exists!"


class InvalidGridError(ValidationError):
  def __init__(self, grid: TextGrid) -> None:
    super().__init__()
    self.grid = grid

  @classmethod
  def validate(cls, grid: TextGrid):
    if not check_is_valid_grid(grid):
      return cls(grid)
    return None

  @property
  def default_message(self) -> str:
    return "Grid is not valid!"


class BoundaryError(ValidationError):
  def __init__(self, timepoints: OrderedSet[float], tiers: Iterable[IntervalTier]) -> None:
    super().__init__()
    self.timepoints = timepoints
    self.tiers = tiers

  @classmethod
  def validate(cls, timepoints: OrderedSet[float], tiers: Iterable[IntervalTier]):
    all_tiers_share_timepoints = check_timepoints_exist_on_all_tiers_as_boundaries(
      timepoints, tiers)
    if not all_tiers_share_timepoints:
      return cls(timepoints, tiers)
    return None

  @property
  def default_message(self) -> str:
    msg = "Tier(s) do not share the same interval boundaries!\n"
    msg += "Timepoints (in s):"
    for boundary in self.timepoints:
      msg += f"- {boundary}\n"


class AudioAndGridLengthMismatchError(ValidationError):
  def __init__(self, grid: TextGrid, audio: np.ndarray, sample_rate: int) -> None:
    super().__init__()
    self.grid = grid
    self.audio = audio
    self.sample_rate = sample_rate

  @classmethod
  def validate(cls, grid: TextGrid, audio: np.ndarray, sample_rate: int):
    if s_to_samples(grid.maxTime, sample_rate) != audio.shape[0]:
      return cls(grid, audio, sample_rate)
    return None

  @property
  def default_message(self) -> str:
    return f"Audio length and grid length does not match ({self.audio.shape[0]} vs. {s_to_samples(self.grid.maxTime, self.sample_rate)})"



class NonDistinctTiersError(ValidationError):
  def __init__(self, tier_name: str) -> None:
    super().__init__()
    self.tier_name = tier_name

  @classmethod
  def validate(cls, tier_name1: str, tier_name2: str):
    if tier_name1 == tier_name2:
      return cls(tier_name1)
    return None

  @property
  def default_message(self) -> str:
    return f"Tiers \"{self.tier_name}\" are not distinct!"


class NotMatchingIntervalFormatError(ValidationError):
  def __init__(self, tier: IntervalTier, tier_interval_format: IntervalFormat, string_format: StringFormat, interval: Interval) -> None:
    super().__init__()
    self.tier = tier
    self.tier_interval_format = tier_interval_format
    self.string_format = string_format
    self.interval = interval

  @classmethod
  def validate(cls, tier: IntervalTier, interval_format: IntervalFormat, string_format: StringFormat):
    for interval in cast(Iterable[Interval], tier.intervals):
      if interval_is_None_or_empty(interval):
        continue
      mark = interval.mark
      symbols = string_format.convert_string_to_symbols(mark)
      if interval_format == IntervalFormat.SYMBOL:
        if len(symbols) > 1:
          return cls(tier, interval_format, string_format, interval)
      elif interval_format in (IntervalFormat.SYMBOLS, IntervalFormat.WORD):
        if " " in symbols:
          return cls(tier, interval_format, string_format, interval)
      elif interval_format == IntervalFormat.WORDS:
        continue
      else:
        assert False
    return None

  @property
  def default_message(self) -> str:
    msg = f"Interval marks format does not match {self.tier_interval_format!r}!\n"
    if self.tier_interval_format in (IntervalFormat.SYMBOLS, IntervalFormat.WORD):
      if self.string_format == StringFormat.TEXT:
        msg += "Spaces are not allowed:\n"
      elif self.string_format == StringFormat.SYMBOLS:
        msg += "Double-spaces are not allowed:\n"
      else:
        assert False
    elif self.tier_interval_format == IntervalFormat.SYMBOL:
      msg += "Multiple symbols are not allowed:\n"
    else:
      assert False
    msg += f"{get_interval_readable(self.interval)}"
