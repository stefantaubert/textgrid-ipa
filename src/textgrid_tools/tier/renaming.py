from logging import Logger, getLogger
from typing import Optional

from textgrid import TextGrid

from textgrid_tools.globals import ExecutionResult
from textgrid_tools.helper import get_single_tier
from textgrid_tools.validation import (ExistingTierError, InvalidGridError,
                                       MultipleTiersWithThatNameError, NonDistinctTiersError,
                                       NotExistingTierError)


def rename_tier(grid: TextGrid, tier_name: str, output_tier_name: str, logger: Optional[Logger]) -> ExecutionResult:
  if logger is None:
    logger = getLogger(__name__)

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

  assert len(output_tier_name.strip()) > 0

  tier = get_single_tier(grid, tier_name)
  tier.name = output_tier_name

  return None, True
