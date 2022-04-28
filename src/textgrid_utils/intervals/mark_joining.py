from logging import getLogger
from typing import Generator, Iterable, List, Optional, Set, cast

from text_utils import StringFormat
from textgrid.textgrid import Interval, TextGrid
from textgrid_utils.comparison import check_intervals_are_equal
from textgrid_utils.globals import ExecutionResult
from textgrid_utils.helper import get_all_tiers
from textgrid_utils.interval_format import IntervalFormat
from textgrid_utils.intervals.common import (group_adjacent_pauses,
                                             merge_intervals,
                                             replace_intervals)
from textgrid_utils.validation import (InvalidGridError,
                                       InvalidStringFormatIntervalError,
                                       NotExistingTierError,
                                       NotMatchingIntervalFormatError)


def join_marks(grid: TextGrid, tier_names: Set[str], tiers_string_format: StringFormat, tiers_interval_format: IntervalFormat, empty: bool, marks: Set[str]) -> ExecutionResult:
  assert len(tier_names) > 0
  assert empty or len(marks) > 0

  if error := InvalidGridError.validate(grid):
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

  joined_count = 0
  joined_to_count = 0
  ignored_count = 0

  changed_anything = False
  for tier in tiers:
    intervals_copy = cast(Iterable[Interval], list(tier.intervals))
    for chunk in chunk_intervals(intervals_copy, empty, marks):
      merged_interval = merge_intervals(chunk, tiers_string_format, tiers_interval_format)
      replace_with = [merged_interval]
      if not check_intervals_are_equal(chunk, replace_with):
        joined_count += len(chunk)
        joined_to_count += len(replace_with)
        replace_intervals(tier, chunk, replace_with)
        changed_anything = True
      else:
        ignored_count += len(chunk)
  logger = getLogger(__name__)
  logger.info(
    f"Joined {joined_count} intervals to {joined_to_count} intervals. Didn't joined {ignored_count} intervals.")
  return None, changed_anything


def chunk_intervals(intervals: Iterable[Interval], empty: bool, marks: Set[str]) -> Generator[List[Interval], None, None]:
  chunk = []
  intervals_with_grouped_pauses = group_adjacent_pauses(intervals)
  for interval_or_pause_group in intervals_with_grouped_pauses:
    is_pause = isinstance(interval_or_pause_group, list)
    if is_pause:
      if empty:
        # extend because they should be merged
        chunk.extend(interval_or_pause_group)
      else:
        if len(chunk) > 0:
          yield chunk
          chunk = []
        for pause_interval in interval_or_pause_group:
          # yield each because they should not be merged
          yield [pause_interval]
    else:
      assert isinstance(interval_or_pause_group, Interval)
      interval = interval_or_pause_group
      if interval.mark in marks:
        chunk.append(interval)
      else:
        if len(chunk) > 0:
          yield chunk
          chunk = []
        yield [interval]

  if len(chunk) > 0:
    yield chunk
