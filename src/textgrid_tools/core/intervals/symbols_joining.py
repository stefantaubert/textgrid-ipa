from typing import Generator, Iterable, List, Optional, Set, cast

from ordered_set import OrderedSet
from text_utils import StringFormat, Symbol
from text_utils.pronunciation.ipa2symb import merge_left_core, merge_right_core
from textgrid.textgrid import Interval, TextGrid
from textgrid_tools.core.comparison import check_intervals_are_equal
from textgrid_tools.core.globals import ExecutionResult
from textgrid_tools.core.helper import get_all_tiers, get_mark
from textgrid_tools.core.interval_format import IntervalFormat
from textgrid_tools.core.intervals.common import (
    merge_intervals_custom_symbol, replace_intervals)
from textgrid_tools.core.validation import (InvalidGridError,
                                            InvalidStringFormatIntervalError,
                                            NotExistingTierError,
                                            NotMatchingIntervalFormatError,
                                            ValidationError)


class InvalidModeError(ValidationError):
  def __init__(self, mode: str) -> None:
    super().__init__()
    self.mode = mode

  @classmethod
  def validate(cls, mode: str):
    if mode not in ["right", "left"]:
      return cls(mode)
    return None

  @property
  def default_message(self) -> str:
    return "Mode needs to be 'right' or 'left'!"


def join_interval_symbols(grid: TextGrid, tier_names: Set[str], tiers_string_format: StringFormat, tiers_interval_format: IntervalFormat, custom_join_symbol: Optional[Symbol], join_symbols: OrderedSet[Symbol], ignore_join_symbols: OrderedSet[Symbol], mode: str) -> ExecutionResult:
  assert len(tier_names) > 0

  if error := InvalidGridError.validate(grid):
    return error, False

  if error := InvalidModeError.validate(mode):
    return error, False

  for tier_name in tier_names:
    if error := NotExistingTierError.validate(grid, tier_name):
      return error, False

  tiers = list(get_all_tiers(grid, tier_names))

  for tier in tiers:
    if error := InvalidStringFormatIntervalError.validate_tier(tier, tiers_string_format):
      return error, False

    if error := NotMatchingIntervalFormatError.validate_tier(tier, tiers_interval_format, tiers_string_format):
      return error, False

  changed_anything = False
  for tier in tiers:
    intervals_copy = cast(List[Interval], list(tier.intervals))
    for chunk in chunk_intervals(intervals_copy, join_symbols, ignore_join_symbols, mode):
      merged_interval = merge_intervals_custom_symbol(
        chunk, tiers_string_format, custom_join_symbol)
      if not check_intervals_are_equal(chunk, [merged_interval]):
        replace_intervals(tier, chunk, [merged_interval])
        changed_anything = True

  return None, changed_anything


def chunk_intervals(intervals: List[Interval], join_symbols: OrderedSet[Symbol], ignore_join_symbols: OrderedSet[Symbol], mode: str) -> Generator[List[Interval], None, None]:
  intervals_as_symbols = tuple(
    get_mark(interval) for interval in intervals
  )

  if mode == "right":
    tmp = merge_right_core(intervals_as_symbols, join_symbols, ignore_join_symbols)
  elif mode == "left":
    tmp = merge_left_core(intervals_as_symbols, join_symbols, ignore_join_symbols)
  else:
    assert False

  for merged_symbols in tmp:
    assert len(merged_symbols) > 0
    chunk = []
    for symbol in merged_symbols:
      interval = intervals.pop(0)
      assert interval.mark == symbol
      chunk.append(interval)
    yield chunk
  assert len(intervals) == 0
