from logging import getLogger
from math import inf
from typing import Generator, Iterable, List, Optional, Union

from text_utils import StringFormat
from textgrid.textgrid import Interval, IntervalTier, TextGrid
from textgrid_tools.core.globals import ExecutionResult
from textgrid_tools.core.intervals.joining.common import merge_intervals
from textgrid_tools.core.mfa.helper import (add_or_update_tier,
                                            check_is_valid_grid,
                                            get_first_tier,
                                            get_intervals_duration,
                                            interval_is_None_or_whitespace,
                                            tier_exists)
from textgrid_tools.core.mfa.interval_format import IntervalFormat
from textgrid_tools.core.validation import (ExistingTierError,
                                            InvalidGridError,
                                            NotExistingTierError,
                                            NotMatchingIntervalFormatError)


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


def join_intervals(grid: TextGrid, tier_name: str, tier_string_format: StringFormat, tier_interval_format: IntervalFormat, join_pauses_under_duration: float = inf, custom_output_tier_name: Optional[str] = None, overwrite_tier: bool = True) -> ExecutionResult:
  if error := InvalidGridError.validate(grid):
    return error, False

  if error := NotExistingTierError.validate(grid, tier_name):
    return error, False

  output_tier_name = tier_name
  if custom_output_tier_name is not None:
    if not overwrite_tier and (error := ExistingTierError.validate(grid, custom_output_tier_name)):
      return error, False
    output_tier_name = custom_output_tier_name

  tier = get_first_tier(grid, tier_name)

  if error := NotMatchingIntervalFormatError.validate_tier(tier, tier_interval_format, tier_string_format):
    return error, False

  target_intervals = (
    merge_intervals(chunk, tier_string_format, tier_interval_format)
    for chunked_interval in chunk_intervals(tier.intervals, join_pauses_under_duration)
    for chunk in chunked_interval
  )

  output_tier = IntervalTier(
    name=output_tier_name,
    minTime=tier.minTime,
    maxTime=tier.maxTime,
  )

  output_tier.intervals.extend(target_intervals)

  changed_anything = add_or_update_tier(grid, tier, output_tier, overwrite_tier)

  return None, changed_anything


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
