from logging import getLogger
from typing import Set

from text_utils.string_format import StringFormat
from text_utils.types import Symbol
from text_utils.utils import symbols_ignore
from textgrid.textgrid import TextGrid
from textgrid_tools.core.globals import ExecutionResult
from textgrid_tools.core.helper import get_all_intervals, get_mark_symbols
from textgrid_tools.core.validation import (InvalidGridError,
                                            InvalidStringFormatIntervalError,
                                            NotExistingTierError)


def remove_symbols(grid: TextGrid, tier_names: Set[str], tiers_string_format: StringFormat, symbols: Set[Symbol]) -> ExecutionResult:
  assert len(symbols) > 0
  assert len(tier_names) > 0

  if error := InvalidGridError.validate(grid):
    return error, False

  for tier_name in tier_names:
    if error := NotExistingTierError.validate(grid, tier_name):
      return error, False

  intervals = list(get_all_intervals(grid, tier_names))

  if error := InvalidStringFormatIntervalError.validate_intervals(intervals, tiers_string_format):
    return error, False

  logger = getLogger(__name__)
  logger.debug(f"Removing symbols: {' '.join(sorted(symbols))}...")

  changed_anything = False

  for interval in intervals:
    interval_symbols = get_mark_symbols(interval, tiers_string_format)
    interval_symbols = symbols_ignore(interval_symbols, symbols)
    mark = tiers_string_format.convert_symbols_to_string(interval_symbols)
    if interval.mark != mark:
      logger.debug(f"Changed \"{interval.mark}\" to \"{mark}\".")
      interval.mark = mark
      changed_anything = True

  return None, changed_anything
