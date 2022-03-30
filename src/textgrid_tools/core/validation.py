from collections import OrderedDict
from typing import Iterable, Optional
from typing import OrderedDict as ODType

import numpy as np
from audio_utils.audio import s_to_samples
from ordered_set import OrderedSet
from text_utils.string_format import (StringFormat,
                                      can_convert_symbols_string_to_symbols)
from textgrid.textgrid import Interval, IntervalTier, TextGrid
from textgrid_tools.core.helper import (
    check_is_valid_grid, check_timepoints_exist_on_all_tiers_as_boundaries,
    get_count_of_tiers, get_interval_readable, get_mark, get_mark_symbols,
    get_tier_readable, tier_exists, timepoint_is_boundary)
from textgrid_tools.core.interval_format import IntervalFormat


class ValidationError():
  # pylint: disable=no-self-use
  @property
  def default_message(self) -> str:
    return ""


# class NoTiersDefinedError(ValidationError):
#   @classmethod
#   def validate(cls, tiers: Set[str]):
#     if len(tiers) == 0:
#       return cls()
#     return None

#   @property
#   def default_message(self) -> str:
#     return "No tiers were defined!"

class InternalError(ValidationError):
  @property
  def default_message(self) -> str:
    return "Internal error!"


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


class MultipleTiersWithThatNameError(ValidationError):
  def __init__(self, grid: TextGrid, tier_name: str) -> None:
    super().__init__()
    self.grid = grid
    self.tier_name = tier_name

  @classmethod
  def validate(cls, grid: TextGrid, tier_name: str):
    if get_count_of_tiers(grid, tier_name) > 1:
      return cls(grid, tier_name)
    return None

  @property
  def default_message(self) -> str:
    return f"Grid contains multiple tiers with name \"{self.tier_name}\"!"


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
  def __init__(self, timepoints: OrderedSet[float], tiers: Iterable[IntervalTier], non_existent_boundaries: ODType[float, OrderedSet[str]]) -> None:
    super().__init__()
    self.timepoints = timepoints
    self.tiers = tiers
    self.non_existent_boundaries = non_existent_boundaries

  @classmethod
  def validate(cls, timepoints: OrderedSet[float], tiers: Iterable[IntervalTier]):
    non_existent_boundaries: ODType[float, OrderedSet[str]] = OrderedDict()
    tiers = list(tiers)
    for timepoint in timepoints:
      for tier in tiers:
        if not timepoint_is_boundary(timepoint, tier):
          if timepoint not in non_existent_boundaries:
            non_existent_boundaries[timepoint] = OrderedSet()
          non_existent_boundaries[timepoint].add(tier.name)
    if not len(non_existent_boundaries) == 0:
      return cls(timepoints, tiers, non_existent_boundaries)
    return None

  @property
  def default_message(self) -> str:
    msg = "Tier(s) do not share the same interval boundaries!\n"
    msg += "Non-existent timepoints (in s) on tiers:\n"
    for timepoint, tiers in self.non_existent_boundaries.items():
      msg += f"- {timepoint} does not exist on {', '.join(tiers)}\n"
    return msg


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


class InvalidStringFormatIntervalError(ValidationError):
  def __init__(self, string: str, string_format: StringFormat) -> None:
    super().__init__()
    self.string = string
    self.string_format = string_format
    self.interval: Optional[Interval] = None
    self.tier: Optional[IntervalTier] = None

  @classmethod
  def validate(cls, string: str, string_format: StringFormat):
    if string_format == StringFormat.SYMBOLS:
      if not can_convert_symbols_string_to_symbols(string):
        return cls(string, string_format)
    return None

  @classmethod
  def validate_interval(cls, interval: Interval, string_format: StringFormat):
    mark = get_mark(interval)
    if error := cls.validate(mark, string_format):
      error.interval = interval
      return error
    return None

  @classmethod
  def validate_intervals(cls, intervals: Iterable[Interval], string_format: StringFormat):
    for interval in intervals:
      if error := cls.validate_interval(interval, string_format):
        return error
    return None

  @classmethod
  def validate_tier(cls, tier: IntervalTier, string_format: StringFormat):
    if error := cls.validate_intervals(tier.intervals, string_format):
      error.tier = tier
      return error
    return None

  @property
  def default_message(self) -> str:
    msg = f"Marks format does not match!"
    if self.interval is not None:
      msg += f"\n@{get_interval_readable(self.interval)}"
    if self.tier is not None:
      msg += f"\n@{get_tier_readable(self.tier)}"
    msg += "\n"
    msg += f"Format: {self.string_format!r}\n"
    msg += f"String:\n\n```\n{self.string}\n```"
    return msg


class NotMatchingIntervalFormatError(ValidationError):
  def __init__(self, tier_interval_format: IntervalFormat, string_format: StringFormat, interval: Interval) -> None:
    super().__init__()
    self.tier_interval_format = tier_interval_format
    self.string_format = string_format
    self.interval = interval
    self.tier: Optional[IntervalTier] = None

  @classmethod
  def validate(cls, interval: Interval, interval_format: IntervalFormat, string_format: StringFormat):
    symbols = get_mark_symbols(interval, string_format)
    if interval_format == IntervalFormat.SYMBOL:
      if len(symbols) > 1:
        return cls(interval_format, string_format, interval)
    elif interval_format in (IntervalFormat.SYMBOLS, IntervalFormat.WORD):
      if " " in symbols:
        return cls(interval_format, string_format, interval)
    elif interval_format == IntervalFormat.WORDS:
      return None
    else:
      assert False
    return None

  @classmethod
  def validate_tier(cls, tier: IntervalTier, interval_format: IntervalFormat, string_format: StringFormat):
    for interval in tier.intervals:
      if error := cls.validate(interval, interval_format, string_format):
        error.tier = tier
        return error
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
    if self.tier is not None:
      msg += f"\n{get_tier_readable(self.tier)}"
    return msg
