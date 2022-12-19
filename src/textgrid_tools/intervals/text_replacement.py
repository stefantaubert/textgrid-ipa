import re
from logging import Logger, getLogger
from typing import Optional, Set

from textgrid import TextGrid
from textgrid.textgrid import TextGrid

from textgrid_tools.globals import ExecutionResult
from textgrid_tools.helper import get_all_intervals
from textgrid_tools.validation import InvalidGridError, NotExistingTierError


def replace_text(grid: TextGrid, tier_names: Set[str], pattern: re.Pattern, replace_with: str, logger: Optional[Logger]) -> ExecutionResult:
  if logger is None:
    logger = getLogger(__name__)

  if error := InvalidGridError.validate(grid):
    return error, False

  for tier_name in tier_names:
    if error := NotExistingTierError.validate(grid, tier_name):
      return error, False

  intervals = list(get_all_intervals(grid, tier_names))

  count_changed = 0
  count_unchanged = 0

  for interval in intervals:
    updated_mark = re.sub(pattern, replace_with, interval.mark)
    if updated_mark != interval.mark:
      old_mark = interval.mark
      interval.mark = updated_mark
      logger.debug(f"Replaced \"{old_mark}\" with \"{updated_mark}\".")
      count_changed += 1
    else:
      count_unchanged += 1

  total_count = len(intervals)
  if total_count == 0:
    logger.info("Found no intervals.")
  else:
    logger.info(
      f"Changed {count_changed}/{total_count} ({count_changed/total_count*100:.2f}%) intervals.")

  return None, count_changed > 0
