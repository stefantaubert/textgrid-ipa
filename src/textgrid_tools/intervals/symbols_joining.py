from logging import Logger, getLogger
from typing import Generator, List, Optional, Set, Tuple, cast

from ordered_set import OrderedSet
from textgrid.textgrid import Interval, TextGrid

from textgrid_tools.comparison import check_intervals_are_equal
from textgrid_tools.globals import ExecutionResult
from textgrid_tools.helper import get_all_tiers, get_mark
from textgrid_tools.intervals.common import merge_intervals, replace_intervals
from textgrid_tools.validation import InvalidGridError, NotExistingTierError, ValidationError


class InvalidModeError(ValidationError):
  def __init__(self, mode: str) -> None:
    super().__init__()
    self.mode = mode

  @classmethod
  def validate(cls, mode: str):
    if mode not in ["right", "left", "together"]:
      return cls(mode)
    return None

  @property
  def default_message(self) -> str:
    return "Mode needs to be 'right', 'left' or 'together'!"


def join_interval_symbols(grid: TextGrid, tier_names: Set[str], join_with: str, join_symbols: OrderedSet[str], ignore_join_symbols: OrderedSet[str], mode: str, ignore_empty: bool, logger: Optional[Logger]) -> ExecutionResult:
  assert len(tier_names) > 0
  if logger is None:
    logger = getLogger(__name__)

  if error := InvalidGridError.validate(grid):
    return error, False

  if error := InvalidModeError.validate(mode):
    return error, False

  for tier_name in tier_names:
    if error := NotExistingTierError.validate(grid, tier_name):
      return error, False

  tiers = list(get_all_tiers(grid, tier_names))

  changed_anything = False
  for tier in tiers:
    intervals_copy = cast(List[Interval], list(tier.intervals))
    for chunk in chunk_intervals(intervals_copy, join_symbols, ignore_join_symbols, mode):
      merged_interval = merge_intervals(chunk, join_with, ignore_empty)
      if not check_intervals_are_equal(chunk, [merged_interval]):
        replace_intervals(tier, chunk, [merged_interval])
        changed_anything = True

  return None, changed_anything


def chunk_intervals(intervals: List[Interval], join_symbols: Set[str], ignore_join_symbols: Set[str], mode: str) -> Generator[List[Interval], None, None]:
  intervals_as_symbols = tuple(
    get_mark(interval) for interval in intervals
  )

  if mode == "right":
    tmp = merge_right_core(intervals_as_symbols, join_symbols, ignore_join_symbols)
  elif mode == "left":
    tmp = merge_left_core(intervals_as_symbols, join_symbols, ignore_join_symbols)
  elif mode == "together":
    tmp = merge_together(intervals_as_symbols, join_symbols)
  else:
    assert False

  intervals = list(intervals)
  for merged_symbols in tmp:
    assert len(merged_symbols) > 0
    chunk = []
    for symbol in merged_symbols:
      interval = intervals.pop(0)
      assert interval.mark == symbol
      chunk.append(interval)
    yield chunk
  assert len(intervals) == 0


def merge_together(symbols: Tuple[str, ...], join: Set[str]) -> List[Tuple[str, ...]]:
  current_chunk = []
  for symbol in symbols:
    if symbol in join:
      current_chunk.append(symbol)
    else:
      if len(current_chunk) > 0:
        yield current_chunk
        current_chunk = []
      yield [symbol]

  if len(current_chunk) > 0:
    yield current_chunk


def merge_left_core(symbols: Tuple[str, ...], merge_symbols: Set[str], ignore_merge_symbols: Set[str]) -> Tuple[Tuple[str, ...]]:
  j = 0
  reversed_symbols = symbols[::-1]
  reversed_merged_symbols = []
  while j < len(reversed_symbols):
    new_symbol, j = get_next_merged_left_symbol_and_index(
      reversed_symbols, j, merge_symbols, ignore_merge_symbols)
    reversed_merged_symbols.append(new_symbol)
  merged_symbols = reversed_merged_symbols[::-1]
  return tuple(merged_symbols)


def get_next_merged_left_symbol_and_index(symbols: Tuple[str, ...], j: int, merge_symbols: Set[str], ignore_merge_symbols: Set[str]) -> Tuple[str, int]:
  new_symbol = [symbols[j]]
  j += 1
  if new_symbol[0] not in ignore_merge_symbols and new_symbol[0] not in merge_symbols:
    while j < len(symbols) and symbols[j] in merge_symbols:
      new_symbol.insert(0, symbols[j])
      j += 1
  return tuple(new_symbol), j


def merge_right_core(symbols: Tuple[str, ...], merge_symbols: Set[str], ignore_merge_symbols: Set[str]) -> Tuple[Tuple[str, ...]]:
  j = 0
  merged_symbols = []
  while j < len(symbols):
    new_symbol, j = get_next_merged_right_symbol_and_index(
      symbols, j, merge_symbols, ignore_merge_symbols)
    merged_symbols.append(new_symbol)
  return tuple(merged_symbols)


def get_next_merged_right_symbol_and_index(symbols: Tuple[str, ...], j: int, merge_symbols: Set[str], ignore_merge_symbols: Set[str]) -> Tuple[str, int]:
  new_symbol = [symbols[j]]
  j += 1
  if new_symbol[0] not in ignore_merge_symbols and new_symbol[0] not in merge_symbols:
    while j < len(symbols) and symbols[j] in merge_symbols:
      new_symbol.append(symbols[j])
      j += 1
  return tuple(new_symbol), j


# def merge_right_core2(symbols: Tuple[str, ...], merge_symbols: Set[str], ignore_merge_symbols: Set[str]) -> Tuple[Tuple[str, ...]]:
#   j = 0
#   merged_symbols = []
#   while j < len(symbols):
#     new_symbol = [symbols[j]]
#     j += 1
#     if new_symbol[0] not in ignore_merge_symbols and new_symbol[0] not in merge_symbols:
#       while j < len(symbols) and symbols[j] in merge_symbols:
#         if len(new_symbol) >= 2 and symbols[j] in ignore_merge_symbols:
#           break
#         new_symbol.append(symbols[j])
#         j += 1
#     new_symbol = tuple(new_symbol)
#     merged_symbols.append(new_symbol)
#   return tuple(merged_symbols)
