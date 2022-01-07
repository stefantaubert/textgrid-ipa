from typing import Set

from text_utils.string_format import StringFormat, get_other_format
from textgrid.textgrid import TextGrid
from textgrid_tools.core.globals import ExecutionResult
from textgrid_tools.core.helper import get_all_intervals, get_mark_symbols
from textgrid_tools.core.validation import (InvalidGridError,
                                            InvalidStringFormatIntervalError,
                                            NotExistingTierError)


def switch_string_format(grid: TextGrid, tier_names: Set[str], tiers_string_format: StringFormat) -> ExecutionResult:
  assert len(tier_names) > 0

  if error := InvalidGridError.validate(grid):
    return error, False

  for tier_name in tier_names:
    if error := NotExistingTierError.validate(grid, tier_name):
      return error, False

  intervals = list(get_all_intervals(grid, tier_names))

  if error := InvalidStringFormatIntervalError.validate_intervals(intervals, tiers_string_format):
    return error, False

  changed_anything = False

  target_format = get_other_format(tiers_string_format)

  for interval in intervals:
    symbols = get_mark_symbols(interval, tiers_string_format)
    mark = target_format.convert_symbols_to_string(symbols)

    if interval.mark != mark:
      interval.mark = mark
      changed_anything = True

  return None, changed_anything
