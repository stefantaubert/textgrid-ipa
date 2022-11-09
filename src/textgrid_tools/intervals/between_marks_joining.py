from logging import Logger, getLogger
from typing import Generator, Iterable, List, Optional, Set, cast

from textgrid.textgrid import Interval, TextGrid

from textgrid_tools.comparison import check_intervals_are_equal
from textgrid_tools.globals import ExecutionResult
from textgrid_tools.helper import get_all_tiers, get_intervals_duration
from textgrid_tools.intervals.common import (group_adjacent_intervals, merge_intervals,
                                             replace_intervals)
from textgrid_tools.validation import InvalidGridError, NotExistingTierError, ValidationError


class IgnoreAdjBelowTooLow(ValidationError):
  def __init__(self, pause: float) -> None:
    super().__init__()
    self.pause = pause

  @classmethod
  def validate(cls, pause: float):
    if not pause >= 0:
      return cls(pause)
    return None

  @property
  def default_message(self) -> str:
    return f"Ignore below needs to be greater than or equal to zero but was \"{self.pause}\"!"


def join_intervals_between_marks(grid: TextGrid, tier_names: Set[str], marks: Set[str], ignore_adj_below: float, join_with: str, ignore_empty: bool, logger: Optional[Logger]) -> ExecutionResult:
  assert len(tier_names) > 0
  assert len(marks) > 0

  if logger is None:
    logger = getLogger(__name__)

  if error := InvalidGridError.validate(grid):
    return error, False

  if error := IgnoreAdjBelowTooLow.validate(ignore_adj_below):
    return error, False

  for tier_name in tier_names:
    if error := NotExistingTierError.validate(grid, tier_name):
      return error, False

  tiers = list(get_all_tiers(grid, tier_names))

  changed_anything = False
  for tier in tiers:
    intervals_copy = cast(Iterable[Interval], list(tier.intervals))
    for chunk in chunk_intervals(intervals_copy, ignore_adj_below, marks):
      merged_interval = merge_intervals(chunk, join_with, ignore_empty)
      if not check_intervals_are_equal(chunk, [merged_interval]):
        replace_intervals(tier, chunk, [merged_interval])
        changed_anything = True

  return None, changed_anything


def chunk_intervals(intervals: Iterable[Interval], ignore_adj_under: float, marks: Set[str]) -> Generator[List[Interval], None, None]:
  chunk = []
  intervals_with_grouped_marks = group_adjacent_intervals(intervals, marks)
  for interval_or_mark_group in intervals_with_grouped_marks:
    is_grouped = isinstance(interval_or_mark_group, list)
    if is_grouped:
      if get_intervals_duration(interval_or_mark_group) <= ignore_adj_under:
        # extend because they should be merged
        chunk.extend(interval_or_mark_group)
      else:
        if len(chunk) > 0:
          yield chunk
          chunk = []
        for mark_interval in interval_or_mark_group:
          # yield each because they should not be merged
          yield [mark_interval]
    else:
      assert isinstance(interval_or_mark_group, Interval)
      chunk.append(interval_or_mark_group)

  if len(chunk) > 0:
    yield chunk
