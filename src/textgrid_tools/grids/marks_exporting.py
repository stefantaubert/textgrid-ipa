from logging import Logger, getLogger
from typing import List, Optional, Tuple

from textgrid import TextGrid

from textgrid_tools.globals import ExecutionResult
from textgrid_tools.helper import get_mark, get_single_tier, number_prepend_zeros
from textgrid_tools.validation import InvalidGridError, NotExistingTierError


def get_marks_txt(grids: List[TextGrid], tier_name: str, interval_sep: Optional[str], logger: Optional[Logger]) -> Tuple[ExecutionResult, Optional[str]]:
  if logger is None:
    logger = getLogger(__name__)

  for grid in grids:
    if error := InvalidGridError.validate(grid):
      return (error, False), None

    if error := NotExistingTierError.validate(grid, tier_name):
      return (error, False), None
  if interval_sep is None:
    interval_sep = ""

  result = []
  for nr, grid in enumerate(grids, start=1):
    nr_str = number_prepend_zeros(nr, len(grids))
    tier = get_single_tier(grid, tier_name)
    marks = (get_mark(interval) for interval in tier.intervals)
    marks = (repr(mark)[1:-1] for mark in marks)
    tier_text = interval_sep.join(marks)
    tier_text = f"{nr_str}: {interval_sep}{tier_text}{interval_sep} #{len(tier.intervals)}"
    result.append(tier_text)
  result = '\n'.join(result)

  return (None, False), result
