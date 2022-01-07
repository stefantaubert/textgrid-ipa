from textgrid.textgrid import TextGrid
from textgrid_tools.core.globals import ExecutionResult
from textgrid_tools.core.mfa.helper import get_single_tier
from textgrid_tools.core.validation import (ExistingTierError,
                                            InvalidGridError,
                                            InvalidTierNameError,
                                            MultipleTiersWithThatNameError,
                                            NonDistinctTiersError,
                                            NotExistingTierError)


def rename_tier(grid: TextGrid, tier_name: str, output_tier_name: str) -> ExecutionResult:
  if error := InvalidGridError.validate(grid):
    return error, False

  if error := NotExistingTierError.validate(grid, tier_name):
    return error, False

  if error := MultipleTiersWithThatNameError.validate(grid, tier_name):
    return error, False

  if error := NonDistinctTiersError.validate(tier_name, output_tier_name):
    return error, False

  if error := ExistingTierError.validate(grid, output_tier_name):
    return error, False

  if error := InvalidTierNameError.validate(output_tier_name):
    return error, False

  tier = get_single_tier(grid, tier_name)
  tier.name = output_tier_name

  return None, True
