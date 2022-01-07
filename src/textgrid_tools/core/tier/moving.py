from textgrid.textgrid import TextGrid
from textgrid_tools.core.globals import ExecutionResult
from textgrid_tools.core.helper import get_single_tier
from textgrid_tools.core.validation import (InvalidGridError,
                                            MultipleTiersWithThatNameError,
                                            NotExistingTierError,
                                            ValidationError)


class InvalidPositionError(ValidationError):
  def __init__(self, grid: TextGrid, position: int) -> None:
    super().__init__()
    self.grid = grid
    self.position = position

  @classmethod
  def validate(cls, grid: TextGrid, position: int):
    if not 0 <= position < len(grid.tiers):
      return cls(grid, position)
    return None

  @property
  def default_message(self) -> str:
    return f"Position {self.position} is not valid, it needs to be between [0, {len(self.grid.tiers)})."


def move_tier(grid: TextGrid, tier_name: str, position: int) -> ExecutionResult:
  if error := InvalidGridError.validate(grid):
    return error, False

  if error := NotExistingTierError.validate(grid, tier_name):
    return error, False

  if error := MultipleTiersWithThatNameError.validate(grid, tier_name):
    return error, False

  if error := InvalidPositionError.validate(grid, position):
    return error, False

  changed_anything = False

  tier = get_single_tier(grid, tier_name)

  if grid.tiers[position] != tier:
    grid.tiers.remove(tier)
    grid.tiers.insert(position, tier)
    changed_anything = True

  return None, changed_anything
