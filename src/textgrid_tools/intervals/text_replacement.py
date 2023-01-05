import re
from itertools import chain
from logging import Logger, getLogger
from typing import Generator, Iterable, List, Literal, Optional, Set, cast

from textgrid import TextGrid
from textgrid.textgrid import Interval, IntervalTier, TextGrid

from textgrid_tools.globals import ExecutionResult
from textgrid_tools.helper import get_single_tier
from textgrid_tools.validation import InvalidGridError, NotExistingTierError


def replace_text(grid: TextGrid, tier_names: Set[str], pattern: re.Pattern, replace_with: str, mode: Literal["all", "begin", "end", "both"], logger: Optional[Logger]) -> ExecutionResult:
  if logger is None:
    logger = getLogger(__name__)

  if error := InvalidGridError.validate(grid):
    return error, False

  assert len(tier_names) > 0
  for tier_name in tier_names:
    if error := NotExistingTierError.validate(grid, tier_name):
      return error, False

  count_intervals_changed = 0
  total_interval_count = 0

  intervals_with_matches = None
  for tier_name in tier_names:
    tier = get_single_tier(grid, tier_name)
    matching_intervals = get_intervals_mode(tier, pattern, mode)
    if intervals_with_matches is None:
      intervals_with_matches = matching_intervals
    else:
      intervals_with_matches = chain(intervals_with_matches, matching_intervals)
    total_interval_count += len(tier.intervals)

  assert intervals_with_matches is not None

  for interval in intervals_with_matches:
    updated_mark = re.sub(pattern, replace_with, interval.mark)
    mark_has_changed_after_sub = updated_mark != interval.mark
    if mark_has_changed_after_sub:
      old_mark = interval.mark
      interval.mark = updated_mark
      logger.debug(f"Replaced \"{old_mark}\" with \"{updated_mark}\".")
      count_intervals_changed += 1

  assert total_interval_count > 0
  logger.info(
    f"Changed {count_intervals_changed}/{total_interval_count} intervals ({count_intervals_changed/total_interval_count*100:.2f}%).")

  return None, count_intervals_changed > 0


def get_intervals_begin(tier: List[Interval], pattern: re.Pattern) -> Generator[Interval, None, None]:
  for interval in tier.intervals:
    if len(re.findall(pattern, interval.mark)) > 0:
      yield interval
      continue
    break


def get_intervals_end(intervals: List[Interval], pattern: re.Pattern) -> Generator[Interval, None, None]:
  for interval in reversed(intervals):
    if len(re.findall(pattern, interval.mark)) > 0:
      yield interval
      continue
    break


def get_intervals_both(intervals: List[Interval], pattern: re.Pattern) -> Generator[Interval, None, None]:
  begin_intervals = list(get_intervals_begin(intervals, pattern))
  rest_intervals = intervals[len(begin_intervals):]
  end_intervals = list(get_intervals_end(rest_intervals, pattern))
  yield from begin_intervals
  yield from end_intervals


def get_intervals_all(tier: Iterable[Interval], pattern: re.Pattern) -> Generator[Interval, None, None]:
  for interval in cast(Iterable[Interval], tier.intervals):
    if len(re.findall(pattern, interval.mark)) > 0:
      yield interval


def get_intervals_mode(tier: IntervalTier, pattern: re.Pattern, mode: Literal["all", "begin", "end", "both"]) -> Generator[Interval, None, None]:
  if mode == "all":
    yield from get_intervals_all(tier, pattern)
  elif mode == "begin":
    yield from get_intervals_begin(tier, pattern)
  elif mode == "end":
    yield from get_intervals_end(tier, pattern)
  elif mode == "both":
    yield from get_intervals_both(tier, pattern)
  else:
    assert False
