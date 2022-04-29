from collections import OrderedDict
from typing import Iterable
from typing import OrderedDict as ODType

import numpy as np
from ordered_set import OrderedSet
from textgrid.textgrid import IntervalTier, TextGrid

from textgrid_tools.helper import (check_is_valid_grid, get_count_of_tiers, s_to_samples,
                                   tier_exists, timepoint_is_boundary)


class ValidationError(Exception):
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
