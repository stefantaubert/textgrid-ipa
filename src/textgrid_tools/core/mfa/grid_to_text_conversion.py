from typing import Optional, Tuple

from text_utils import StringFormat
from textgrid.textgrid import TextGrid
from textgrid_tools.core.globals import ExecutionResult
from textgrid_tools.core.intervals.joining.common import merge_intervals
from textgrid_tools.core.mfa.helper import get_single_tier
from textgrid_tools.core.mfa.interval_format import IntervalFormat
from textgrid_tools.core.validation import (InvalidGridError,
                                            MultipleTiersWithThatNameError,
                                            NotExistingTierError)


def convert_tier_to_text(grid: TextGrid, tier_name: str, tier_string_format: StringFormat, tier_interval_format: IntervalFormat) -> Tuple[ExecutionResult, Optional[str]]:
  if error := InvalidGridError.validate(grid):
    return (error, False), None

  if error := NotExistingTierError.validate(grid, tier_name):
    return (error, False), None
    
  if error := MultipleTiersWithThatNameError.validate(grid, tier_name):
    return error, False

  tier = get_single_tier(grid, tier_name)
  result = merge_intervals(tier.intervals, tier_string_format, tier_interval_format).mark

  return (None, False), result
