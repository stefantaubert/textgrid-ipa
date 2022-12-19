from logging import Logger, getLogger
from typing import Generator, Iterable, List, Optional, Set, cast

from textgrid.textgrid import Interval, TextGrid

from textgrid_tools.comparison import check_intervals_are_equal
from textgrid_tools.globals import ExecutionResult
from textgrid_tools.helper import get_all_tiers
from textgrid_tools.intervals.common import merge_intervals, replace_intervals
from textgrid_tools.validation import InvalidGridError, NotExistingTierError


def join_by_template(grid: TextGrid, tier_names: Set[str], join_with: str, ignore_empty: bool, template: List[str], logger: Optional[Logger]) -> ExecutionResult:
  assert len(tier_names) > 0

  if logger is None:
    logger = getLogger(__name__)

  if error := InvalidGridError.validate(grid):
    return error, False

  for tier_name in tier_names:
    if error := NotExistingTierError.validate(grid, tier_name):
      return error, False

  tiers = list(get_all_tiers(grid, tier_names))

  joined_count = 0
  joined_to_count = 0
  ignored_count = 0

  changed_anything = False
  for tier in tiers:
    intervals_copy = cast(Iterable[Interval], list(tier.intervals))
    for chunk in chunk_intervals(intervals_copy, template):
      merged_interval = merge_intervals(chunk, join_with, ignore_empty)
      replace_with = [merged_interval]
      if not check_intervals_are_equal(chunk, replace_with):
        joined_count += len(chunk)
        joined_to_count += len(replace_with)
        replace_intervals(tier, chunk, replace_with)
        changed_anything = True
      else:
        ignored_count += len(chunk)

  logger.info(
    f"Joined {joined_count} intervals to {joined_to_count} intervals. Didn't joined {ignored_count} intervals.")
  return None, changed_anything


def chunk_intervals(intervals: Iterable[Interval], template: List[str]) -> Generator[List[Interval], None, None]:
  chunk = []
  template_i = 0
  for interval in intervals:
    if template[template_i] == interval.mark:
      chunk.append(interval)
      template_i += 1
    else:
      if len(chunk) > 0:
        for c_interval in chunk:
          yield [c_interval]
        chunk = []
        template_i = 0

      if template[template_i] == interval.mark:
        chunk.append(interval)
        template_i += 1
      else:
        yield [interval]
        continue

    template_fulfilled = template_i == len(template)
    if template_fulfilled:
      yield chunk
      chunk = []
      template_i = 0

  if len(chunk) > 0:
    for c_interval in chunk:
      yield [c_interval]
    chunk = []
    template_i = 0
