from logging import Logger, getLogger
from typing import Optional, Set

from textgrid import TextGrid

from textgrid_tools.globals import ExecutionResult
from textgrid_tools.helper import get_all_intervals, is_silence
from textgrid_tools.validation import InvalidGridError, NotExistingTierError


def mark_silence(grid: TextGrid, tier_names: Set[str], min_duration: float, max_duration: float, mark: str, logger: Optional[Logger]) -> ExecutionResult:
  assert min_duration < max_duration
  assert len(mark) > 0
  assert len(tier_names) > 0

  if logger is None:
    logger = getLogger(__name__)

  if error := InvalidGridError.validate(grid):
    return error, False

  for tier_name in tier_names:
    if error := NotExistingTierError.validate(grid, tier_name):
      return error, False

  intervals = list(get_all_intervals(grid, tier_names))

  changed_anything = False
  count_changed = 0
  count_unchanged = 0

  for interval in intervals:
    if is_silence(interval):
      if min_duration <= interval.duration() < max_duration:
        interval.mark = mark
        changed_anything = True
        count_changed += 1
      else:
        count_unchanged += 1
  total_count = count_unchanged + count_changed
  if total_count == 0:
    logger.info("Found no silence intervals.")
  else:
    logger.info(
      f"Marked {count_changed}/{total_count} ({count_changed/total_count*100:.2f}%) silence intervals with '{mark}'.")
  return None, changed_anything
