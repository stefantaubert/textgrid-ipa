from typing import (Any, Dict, Generator, Iterable, List, Optional, Set, Tuple,
                    cast)

from textgrid.textgrid import Interval, IntervalTier, TextGrid
from textgrid_tools.core.globals import ExecutionResult
from textgrid_tools.core.helper import get_mark, get_single_tier
from textgrid_tools.core.validation import (InvalidGridError,
                                            NotExistingTierError)


def get_marks_txt(grids: List[TextGrid], tier_name: str) -> Tuple[ExecutionResult, Optional[str]]:
  for grid in grids:
    if error := InvalidGridError.validate(grid):
      return (error, False), None

    if error := NotExistingTierError.validate(grid, tier_name):
      return (error, False), None

  result = []
  for grid in grids:
    tier = get_single_tier(grid, tier_name)
    marks = (get_mark(interval.mark) for interval in tier.intervals)
    marks = (repr(mark)[1:-1] for mark in marks)
    tier_text = "|".join(marks)
    tier_text = f"|{tier_text}| #{len(tier.intervals)}"
    result.append(tier_text)
  result = '\n'.join(result)

  return (None, False), result
