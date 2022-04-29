from typing import Optional, Tuple

from textgrid.textgrid import TextGrid

from textgrid_utils.globals import ExecutionResult
from textgrid_utils.helper import get_mark, get_single_tier
from textgrid_utils.validation import (InvalidGridError, MultipleTiersWithThatNameError,
                                       NotExistingTierError)


def convert_tier_to_text(grid: TextGrid, tier_name: str, sep: str) -> Tuple[ExecutionResult, Optional[str]]:
  if error := InvalidGridError.validate(grid):
    return (error, False), None

  if error := NotExistingTierError.validate(grid, tier_name):
    return (error, False), None

  if error := MultipleTiersWithThatNameError.validate(grid, tier_name):
    return error, False

  tier = get_single_tier(grid, tier_name)
  marks = (get_mark(interval) for interval in tier.intervals)
  result = sep.join(marks)

  return (None, True), result
