from typing import Generator, List, Set, Tuple, cast

from ordered_set import OrderedSet
from text_utils.pronunciation.ipa2symb import merge_left_core, merge_right_core
from textgrid.textgrid import Interval, TextGrid

from textgrid_utils.comparison import check_intervals_are_equal
from textgrid_utils.globals import ExecutionResult
from textgrid_utils.helper import get_all_tiers, get_mark
from textgrid_utils.intervals.common import merge_intervals, replace_intervals
from textgrid_utils.validation import InvalidGridError, NotExistingTierError, ValidationError


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


def join_interval_symbols(grid: TextGrid, tier_names: Set[str], join_with: str, join_symbols: OrderedSet[str], ignore_join_symbols: OrderedSet[str], mode: str, ignore_empty: bool) -> ExecutionResult:
  assert len(tier_names) > 0

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
