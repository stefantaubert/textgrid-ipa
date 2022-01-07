from logging import getLogger
from typing import Optional, Set

from text_utils import symbols_map_arpa_to_ipa
from text_utils.string_format import StringFormat
from text_utils.types import Symbol
from textgrid.textgrid import TextGrid
from textgrid_tools.core.globals import ExecutionResult
from textgrid_tools.core.helper import get_all_intervals, get_mark_symbols
from textgrid_tools.core.validation import (InvalidGridError,
                                            InvalidStringFormatIntervalError,
                                            NotExistingTierError)


def map_arpa_to_ipa(grid: TextGrid, tier_names: Set[str], tiers_string_format: StringFormat, replace_unknown: bool, replace_unknown_with: Optional[Symbol]) -> ExecutionResult:
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

  changed_anything = False

  for interval in intervals:
    arpa_symbols = get_mark_symbols(interval, tiers_string_format)
    ipa_symbols = symbols_map_arpa_to_ipa(
      arpa_symbols=arpa_symbols,
      ignore={},
      replace_unknown=replace_unknown,
      replace_unknown_with=replace_unknown_with,
    )

    ipa = tiers_string_format.convert_symbols_to_string(ipa_symbols)

    if interval.mark != ipa:
      logger.debug(f"Mapped \"{interval.mark}\" to \"{ipa}\".")
      interval.mark = ipa
      changed_anything = True

  return None, changed_anything
