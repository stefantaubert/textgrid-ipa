from logging import getLogger
from typing import List

from textgrid.textgrid import Interval, IntervalTier, TextGrid
from textgrid_tools.core.mfa.helper import (check_is_valid_grid,
                                            get_first_tier, interval_is_None_or_empty,
                                            tier_exists)
from textgrid_tools.core.mfa.string_format import transform_text_to_symbols


def can_convert_text_to_symbols(grid: TextGrid, tier: str) -> bool:
  logger = getLogger(__name__)
  if not check_is_valid_grid(grid):
    logger.error("Grid is invalid!")
    return False

  if not tier_exists(grid, tier):
    logger.error(f"Tier \"{tier}\" not found!")
    return False

  return True


def convert_text_to_symbols(grid: TextGrid, tier: str, new_tier: str) -> None:
  text_tier = get_first_tier(grid, tier)

  symbols_tier = IntervalTier(
    minTime=text_tier.minTime,
    maxTime=text_tier.maxTime,
    name=new_tier,
  )

  original_text_tier_intervals: List[Interval] = text_tier.intervals
  for interval in original_text_tier_intervals:
    symbols_str = ""

    if not interval_is_None_or_empty(interval):
      symbols_str = transform_text_to_symbols(str(interval.mark))

    symbols_interval = Interval(
      minTime=interval.minTime,
      maxTime=interval.maxTime,
      mark=symbols_str,
    )

    symbols_tier.addInterval(symbols_interval)

  grid.append(symbols_tier)
