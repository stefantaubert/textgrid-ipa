from logging import getLogger
from typing import Generator, Iterable, List, Optional

from text_utils import StringFormat
from textgrid.textgrid import Interval, IntervalTier, TextGrid
from textgrid_tools.core.intervals.joining.common import merge_intervals
from textgrid_tools.core.mfa.helper import (check_is_valid_grid,
                                            get_first_tier,
                                            interval_is_None_or_whitespace,
                                            replace_tier, tier_exists)
from textgrid_tools.core.mfa.interval_format import IntervalFormat


def can_join_intervals(grid: TextGrid, tier_name: str, join_pauses_under_duration: float, output_tier_name: Optional[str], overwrite_tier: bool) -> None:
  logger = getLogger(__name__)

  if not check_is_valid_grid(grid):
    logger.error("Grid is invalid!")
    return False

  if not tier_exists(grid, tier_name):
    logger.error(f"Tier \"{tier_name}\" not found!")
    return False

  if output_tier_name is None:
    output_tier_name = tier_name

  if not join_pauses_under_duration >= 0:
    logger.error("Minimum pause needs to be >= 0!")
    return False

  if tier_exists(grid, output_tier_name) and not overwrite_tier:
    logger.error(f"Tier \"{output_tier_name}\" already exists!")
    return False

  return True


def join_intervals(grid: TextGrid, tier_name: str, tier_string_format: StringFormat, tier_interval_format: IntervalFormat, join_pauses_under_duration: float, output_tier_name: Optional[str] = None, overwrite_tier: bool = True) -> None:
  assert can_join_intervals(grid, tier_name, join_pauses_under_duration,
                            output_tier_name, overwrite_tier)

  if output_tier_name is None:
    output_tier_name = tier_name

  tier = get_first_tier(grid, tier_name)

  new_tier = IntervalTier(
    name=output_tier_name,
    minTime=grid.minTime,
    maxTime=grid.maxTime,
  )

  chunks = get_chunks(tier.intervals, join_pauses_under_duration)

  for chunk in chunks:
    interval = merge_intervals(chunk, tier_string_format, tier_interval_format)
    new_tier.addInterval(interval)

  if overwrite_tier and tier.name == new_tier.name:
    replace_tier(tier, new_tier)
  elif overwrite_tier and tier_exists(grid, new_tier.name):
    existing_tier = get_first_tier(grid, new_tier.name)
    replace_tier(existing_tier, new_tier)
  else:
    grid.append(new_tier)


def get_chunks(intervals: Iterable[Interval], min_pause_s: float) -> Generator[List[Interval], None, None]:
  chunk = []
  chunk_is_only_pause = False
  for interval in intervals:
    is_empty = interval_is_None_or_whitespace(interval)
    if is_empty:
      if interval.duration() < min_pause_s:
        chunk.append(interval)
      else:
        if len(chunk) > 0:
          yield chunk
          chunk = []
        yield [interval]
    else:
      chunk.append(interval)

  if len(chunk) > 0:
    yield chunk
