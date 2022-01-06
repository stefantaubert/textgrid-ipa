from logging import getLogger
from math import inf
from typing import Generator, Iterable, List, Optional, Union

from text_utils import StringFormat
from textgrid.textgrid import Interval, IntervalTier, TextGrid
from textgrid_tools.core.mfa.helper import (check_is_valid_grid,
                                            get_first_tier,
                                            get_intervals_duration,
                                            interval_is_None_or_whitespace,
                                            merge_intervals, replace_tier,
                                            tier_exists)
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


def split_intervals(grid: TextGrid, tier_name: str, tier_string_format: StringFormat, tier_interval_format: IntervalFormat, target_interval_format: IntervalFormat, output_tier_name: Optional[str] = None, overwrite_tier: bool = True) -> None:
  
  if output_tier_name is None:
    output_tier_name = tier_name

  tier = get_first_tier(grid, tier_name)

  new_tier = IntervalTier(
    name=output_tier_name,
    minTime=grid.minTime,
    maxTime=grid.maxTime,
  )

  chunked_intervals = chunk_intervals(tier.intervals, join_pauses_under_duration)

  for chunk in chunked_intervals:
    interval = merge_intervals(chunk, tier_string_format, tier_interval_format)
    new_tier.addInterval(interval)

  if overwrite_tier and tier.name == new_tier.name:
    replace_tier(tier, new_tier)
  elif overwrite_tier and tier_exists(grid, new_tier.name):
    existing_tier = get_first_tier(grid, new_tier.name)
    replace_tier(existing_tier, new_tier)
  else:
    grid.append(new_tier)


def chunk_intervals(intervals: Iterable[Interval], min_pause_s: float) -> Generator[List[Interval], None, None]:
  chunk = []
  intervals_with_grouped_pauses = group_adjacent_pauses(intervals)
  for interval_or_pause_group in intervals_with_grouped_pauses:
    is_pause = isinstance(interval_or_pause_group, list)
    if is_pause:
      if get_intervals_duration(interval_or_pause_group) < min_pause_s:
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
      chunk.append(interval_or_pause_group)

  if len(chunk) > 0:
    yield chunk


def group_adjacent_pauses(intervals: Iterable[Interval]) -> Generator[Union[Interval, List[Interval]], None, None]:
  pause_group = []
  for interval in intervals:
    is_pause = interval_is_None_or_whitespace(interval)
    if is_pause:
      pause_group.append(interval)
    else:
      if len(pause_group) > 0:
        yield pause_group
        pause_group = []
      yield interval

  if len(pause_group) > 0:
    yield pause_group
