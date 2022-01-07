from typing import Set

from text_utils.language import Language
from text_utils.string_format import (StringFormat,
                                      convert_symbols_to_text_string,
                                      convert_text_string_to_symbols)
from text_utils.symbol_format import SymbolFormat
from text_utils.text import text_normalize
from textgrid.textgrid import TextGrid
from textgrid_tools.core.globals import ExecutionResult
from textgrid_tools.core.mfa.helper import get_all_intervals, get_mark_symbols
from textgrid_tools.core.validation import (InvalidGridError,
                                            InvalidStringFormatIntervalError,
                                            NotExistingTierError)


def normalize_tiers(grid: TextGrid, tier_names: Set[str], tiers_string_format: StringFormat, language: Language, text_format: SymbolFormat) -> ExecutionResult:
  assert len(tier_names) > 0
  assert tiers_string_format == StringFormat.TEXT
  assert text_format == SymbolFormat.GRAPHEMES

  if error := InvalidGridError.validate(grid):
    return error, False

  for tier_name in tier_names:
    if error := NotExistingTierError.validate(grid, tier_name):
      return error, False

  intervals = list(get_all_intervals(grid, tier_names))

  if error := InvalidStringFormatIntervalError.validate_intervals(intervals, tiers_string_format):
    return error, False

  changed_anything = False

  for interval in intervals:
    symbols = get_mark_symbols(interval, tiers_string_format)
    text = convert_symbols_to_text_string(symbols)
    text = text.replace("\n", " ")
    text = text.replace("\r", "")
    text = text_normalize(
      text=text,
      lang=language,
      text_format=text_format,
    )
    symbols = convert_text_string_to_symbols(text)
    mark = tiers_string_format.convert_symbols_to_string(symbols)
    if interval.mark != mark:
      interval.mark = mark
      changed_anything = True

  return None, changed_anything
