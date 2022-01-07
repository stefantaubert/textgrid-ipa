from typing import Iterable, Set, cast

from text_utils.string_format import StringFormat
from text_utils.types import Symbol
from text_utils.utils import symbols_ignore
from textgrid.textgrid import Interval, TextGrid
from textgrid_tools.core.globals import ExecutionResult
from textgrid_tools.core.mfa.helper import get_all_tiers, get_mark_symbols
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

  intervals = list(
    interval
    for tier in get_all_tiers(grid, tier_names)
    for interval in cast(Iterable[Interval], tier.intervals)
  )

  for interval in intervals:
    if error := InvalidStringFormatIntervalError.validate(interval, tiers_string_format):
      return error, False

  # logger = getLogger(__name__)
  # logger.info(f"Removing symbols: {' '.join(sorted(symbols))} ...")

  changed_anything = False

  for interval in intervals:
    interval_symbols = get_mark_symbols(interval, tiers_string_format)
    interval_symbols = symbols_ignore(interval_symbols, symbols)
    mark = tiers_string_format.convert_symbols_to_string(interval_symbols)
    if interval.mark != mark:
      interval.mark = mark
      changed_anything = True
      # logger.debug(f"Changed \"{interval.mark}\" to \"{mark}\".")
  return None, changed_anything
