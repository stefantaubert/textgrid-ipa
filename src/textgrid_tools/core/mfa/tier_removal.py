from typing import Set

from textgrid.textgrid import TextGrid
from textgrid_tools.core.globals import ExecutionResult
from textgrid_tools.core.mfa.helper import get_all_tiers
from textgrid_tools.core.validation import (InvalidGridError,
                                            NotExistingTierError)


def remove_tiers(grid: TextGrid, tier_names: Set[str]) -> ExecutionResult:
  assert len(tier_names) > 0
  if error := InvalidGridError.validate(grid):
    return error, False

  for tier_name in tier_names:
    if error := NotExistingTierError.validate(grid, tier_name):
      return error, False

  tiers_to_remove = get_all_tiers(grid, tier_names)

  for tier in tiers_to_remove:
    grid.tiers.remove(tier)

  return None, True
