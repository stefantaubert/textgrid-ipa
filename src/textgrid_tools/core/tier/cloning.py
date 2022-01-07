from ordered_set import OrderedSet
from textgrid.textgrid import TextGrid
from textgrid_tools.core.cloning import copy_tier
from textgrid_tools.core.globals import ExecutionResult
from textgrid_tools.core.helper import get_single_tier
from textgrid_tools.core.validation import (ExistingTierError,
                                            InvalidGridError,
                                            InvalidTierNameError,
                                            MultipleTiersWithThatNameError,
                                            NonDistinctTiersError,
                                            NotExistingTierError)


def clone_tier(grid: TextGrid, tier_name: str, output_tier_names: OrderedSet[str], ignore_marks: bool) -> ExecutionResult:
  assert len(output_tier_names) > 0

  if error := InvalidGridError.validate(grid):
    return error, False

  if error := NotExistingTierError.validate(grid, tier_name):
    return error, False

  if error := MultipleTiersWithThatNameError.validate(grid, tier_name):
    return error, False

  for output_tier_name in output_tier_names:
    if error := NonDistinctTiersError.validate(tier_name, output_tier_name):
      return error, False

    if error := ExistingTierError.validate(grid, output_tier_name):
      return error, False

    if error := InvalidTierNameError.validate(output_tier_name):
      return error, False

  tier = get_single_tier(grid, tier_name)

  for output_tier_name in output_tier_names:
    new_tier = copy_tier(tier, ignore_marks)
    new_tier.name = output_tier_name
    grid.append(new_tier)

  return None, True
