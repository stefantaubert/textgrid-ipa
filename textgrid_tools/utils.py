import os
import re
from logging import Logger
from typing import Optional

from textgrid.textgrid import IntervalTier, TextGrid


def check_paths_ok(in_path: str, out_path: str, logger: Logger) -> bool:
  if not os.path.exists(in_path):
    logger.error("The file couldn't be found!")
    return False

  if in_path == out_path:
    logger.error("Input and output files should be different!")
    return False

  return True


# Regular expression matching whitespace:
_whitespace_re = re.compile(r'\s+')


def collapse_whitespace(text: str) -> str:
  return re.sub(_whitespace_re, ' ', text)


def update_or_add_tier(grid: TextGrid, tier: IntervalTier) -> None:
  existing_tier: Optional[IntervalTier] = grid.getFirst(tier.name)
  if existing_tier is not None:
    existing_tier.intervals.clear()
    existing_tier.intervals.extend(tier.intervals)
    existing_tier.maxTime = tier.maxTime
    existing_tier.minTime = tier.minTime
  else:
    grid.append(tier)
