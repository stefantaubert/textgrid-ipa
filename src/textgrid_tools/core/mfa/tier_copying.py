from typing import Optional

from textgrid.textgrid import TextGrid
from textgrid_tools.core.globals import ExecutionResult
from textgrid_tools.core.mfa.helper import add_or_update_tier, get_first_tier
from textgrid_tools.core.validation import (ExistingTierError,
                                            InvalidGridError,
                                            NotExistingTierError,
                                            ValidationError)


class DifferentGridTimesError(ValidationError):
  def __init__(self, grid: TextGrid, reference_grid: TextGrid) -> None:
    super().__init__()
    self.grid = grid
    self.reference_grid = reference_grid

  @classmethod
  def validate(cls, grid: TextGrid, reference_grid: TextGrid):
    if grid.minTime != reference_grid.minTime or grid.maxTime != reference_grid.maxTime:
      return cls(grid, reference_grid)
    return None

  @property
  def default_message(self) -> str:
    return "Both grids need to have the same minTime and maxTime!"


def copy_tier_to_grid(grid: TextGrid, reference_grid: TextGrid, reference_tier_name: str, custom_output_tier_name: Optional[str], overwrite_tier: bool) -> ExecutionResult:
  if error := InvalidGridError.validate(grid):
    return error, False

  if error := InvalidGridError.validate(reference_grid):
    return error, False

  if error := DifferentGridTimesError.validate(grid, reference_grid):
    return error, False

  if error := NotExistingTierError.validate(grid, reference_tier_name):
    return error, False

  output_tier_name = reference_tier_name
  if custom_output_tier_name is not None:
    if not overwrite_tier and (error := ExistingTierError.validate(grid, custom_output_tier_name)):
      return error, False
    output_tier_name = custom_output_tier_name

  reference_tier = get_first_tier(reference_grid, reference_tier_name)

  reference_tier.name = output_tier_name

  add_or_update_tier(grid, None, reference_tier, overwrite_tier)
