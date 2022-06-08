from logging import Logger, getLogger
from typing import Optional

from textgrid import TextGrid

from textgrid_tools.globals import ExecutionResult
from textgrid_tools.helper import get_single_tier
from textgrid_tools.validation import (InvalidGridError, MultipleTiersWithThatNameError,
                                       NotExistingTierError, ValidationError)


class InvalidPositionError(ValidationError):
  def __init__(self, grid: TextGrid, position: int) -> None:
    super().__init__()
    self.grid = grid
    self.position = position

  @classmethod
  def validate(cls, grid: TextGrid, position: int):
    if not 1 <= position <= len(grid.tiers):
      return cls(grid, position)
    return None

  @property
  def default_message(self) -> str:
    return f"Position {self.position} is not valid, it needs to be between [1, {len(self.grid.tiers)})."


def move_tier(grid: TextGrid, tier_name: str, position_one_based: int, logger: Optional[Logger]) -> ExecutionResult:
  if logger is None:
    logger = getLogger(__name__)

  if error := InvalidGridError.validate(grid):
    return error, False

  if error := NotExistingTierError.validate(grid, tier_name):
    return error, False

  if error := MultipleTiersWithThatNameError.validate(grid, tier_name):
    return error, False

  if error := InvalidPositionError.validate(grid, position_one_based):
    return error, False

  changed_anything = False

  tier = get_single_tier(grid, tier_name)

  position_zero_based = position_one_based - 1
  if grid.tiers[position_zero_based] != tier:
    grid.tiers.remove(tier)
    grid.tiers.insert(position_zero_based, tier)
    changed_anything = True

  return None, changed_anything
