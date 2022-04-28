from typing import Optional

from textgrid.textgrid import TextGrid
from textgrid_utils.cloning import copy_tier
from textgrid_utils.globals import ExecutionResult
from textgrid_utils.helper import check_is_valid_grid, get_single_tier
from textgrid_utils.validation import (ExistingTierError,
                                       InvalidGridError,
                                       MultipleTiersWithThatNameError,
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


def copy_tier_to_grid(reference_grid: TextGrid, reference_tier_name: str, grid: TextGrid, custom_output_tier_name: Optional[str]) -> ExecutionResult:
  # TODO maybe support creation of new grid

  if error := InvalidGridError.validate(reference_grid):
    return error, False

  if error := InvalidGridError.validate(grid):
    return error, False

  if error := DifferentGridTimesError.validate(grid, reference_grid):
    return error, False

  if error := NotExistingTierError.validate(reference_grid, reference_tier_name):
    return error, False

  if error := MultipleTiersWithThatNameError.validate(reference_grid, reference_tier_name):
    return error, False

  output_tier_name = reference_tier_name
  if custom_output_tier_name is not None:
    output_tier_name = custom_output_tier_name

  if error := ExistingTierError.validate(grid, output_tier_name):
    return error, False

  assert len(output_tier_name.strip()) > 0

  reference_tier = get_single_tier(reference_grid, reference_tier_name)

  tier = copy_tier(reference_tier, False)
  tier.name = output_tier_name

  grid.append(tier)
  assert check_is_valid_grid(grid)

  return None, True
