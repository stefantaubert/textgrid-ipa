from typing import Generator, Iterable, List, Set

from text_utils import StringFormat, symbols_endswith, symbols_strip
from textgrid.textgrid import Interval, TextGrid
from textgrid_tools.core.comparison import check_intervals_are_equal
from textgrid_tools.core.globals import ExecutionResult
from textgrid_tools.core.intervals.joining.common import (merge_intervals,
                                                          replace_intervals)
from textgrid_tools.core.mfa.helper import (get_all_tiers, get_mark_symbols,
                                            interval_is_None_or_whitespace)
from textgrid_tools.core.mfa.interval_format import IntervalFormat
from textgrid_tools.core.validation import (InvalidGridError,
                                            InvalidStringFormatIntervalError,
                                            NotExistingTierError,
                                            NotMatchingIntervalFormatError)


def join_intervals(grid: TextGrid, tier_names: Set[str], tiers_string_format: StringFormat, tiers_interval_format: IntervalFormat, strip_symbols: Set[str], punctuation_symbols: Set[str]) -> ExecutionResult:
  assert len(tier_names) > 0

  if error := InvalidGridError.validate(grid):
    return error, False

  for tier_name in tier_names:
    if error := NotExistingTierError.validate(grid, tier_name):
      return error, False

  tiers = list(get_all_tiers(grid, tier_names))

  for tier in tiers:
    if error := InvalidStringFormatIntervalError.validate_tier(tier, tiers_string_format):
      return error, False

    if error := NotMatchingIntervalFormatError.validate(tier, tiers_interval_format, tiers_string_format):
      return error, False

  changed_anything = False
  for tier in tiers:
    for chunk in chunk_intervals(tier.intervals, tiers_string_format, strip_symbols, punctuation_symbols):
      merged_interval = merge_intervals(chunk, tiers_string_format, tiers_interval_format)
      if not check_intervals_are_equal(chunk, [merged_interval]):
        replace_intervals(tier, chunk, [merged_interval])
        changed_anything = True

  return None, changed_anything


def chunk_intervals(intervals: Iterable[Interval], intervals_string_format: StringFormat, strip_symbols: Set[str], punctuation_symbols: Set[str]) -> Generator[List[Interval], None, None]:
  chunk = []
  for interval in intervals:
    interval_is_pause_between_sentences = len(
      chunk) == 0 and interval_is_None_or_whitespace(interval)

    if interval_is_pause_between_sentences:
      yield [interval]
      continue

    chunk.append(interval)

    mark_symbols = get_mark_symbols(interval, intervals_string_format)
    mark_symbols_stripped = symbols_strip(mark_symbols, strip_symbols)
    was_ending = symbols_endswith(mark_symbols_stripped, punctuation_symbols)
    if was_ending:
      yield chunk
      chunk = []

  if len(chunk) > 0:
    yield chunk
