from logging import getLogger
from typing import Generator, Iterable, Iterator, List, Optional

from text_utils import StringFormat
from textgrid.textgrid import Interval, IntervalTier, TextGrid
from textgrid_tools.core.mfa.helper import (check_is_valid_grid,
                                            get_first_tier,
                                            interval_is_None_or_whitespace,
                                            intervals_to_text, replace_tier,
                                            tier_exists)
from textgrid_tools.core.mfa.interval_format import IntervalFormat


def can_join_intervals(grid: TextGrid, tier_name: str, output_tier_name: Optional[str], overwrite_tier: bool) -> None:
  logger = getLogger(__name__)

  if not check_is_valid_grid(grid):
    logger.error("Grid is invalid!")
    return False

  if not tier_exists(grid, tier_name):
    logger.error(f"Tier \"{tier_name}\" not found!")
    return False

  if output_tier_name is None:
    output_tier_name = tier_name

  if tier_exists(grid, output_tier_name) and not overwrite_tier:
    logger.error(f"Tier \"{output_tier_name}\" already exists!")
    return False

  return True


def join_intervals(grid: TextGrid, tier_name: str, tier_string_format: StringFormat, tier_interval_format: IntervalFormat, output_tier_name: Optional[str] = None, overwrite_tier: bool = True) -> None:
  assert can_join_intervals(grid, tier_name, output_tier_name, overwrite_tier)

  if output_tier_name is None:
    output_tier_name = tier_name

  tier = get_first_tier(grid, tier_name)

  interval_iterator: Iterator[Interval] = None

  interval_iterator = join_via_non_pauses(
    tier, tier_string_format, tier_interval_format)

  new_tier = IntervalTier(
    name=output_tier_name,
    minTime=grid.minTime,
    maxTime=grid.maxTime,
  )

  for interval in interval_iterator:
    new_tier.addInterval(interval)

  if overwrite_tier and tier.name == new_tier.name:
    replace_tier(tier, new_tier)
  elif overwrite_tier and tier_exists(grid, new_tier.name):
    existing_tier = get_first_tier(grid, new_tier.name)
    replace_tier(existing_tier, new_tier)
  else:
    grid.append(new_tier)


def join_via_non_pauses(tier: IntervalTier, tier_string_format: StringFormat, interval_format: IntervalFormat) -> Generator[Interval, None, None]:
  assert interval_format in {IntervalFormat.WORDS, IntervalFormat.WORD}
  current_content = []
  chunks: List[List[Interval]] = []
  for interval in tier.intervals:
    if interval_is_None_or_whitespace(interval):
      if len(current_content) > 0:
        chunks.append(current_content)
        current_content = []
      chunks.append([interval])
    else:
      current_content.append(interval)

  if len(current_content) > 0:
    chunks.append(current_content)
    current_content = []

  for chunk in chunks:
    yield merge_intervals(chunk, tier_string_format)


def merge_intervals(intervals: Iterable[Interval], tier_string_format: StringFormat) -> Interval:
  assert len(intervals) > 0
  first_interval = intervals[0]
  last_interval = intervals[-1]
  is_pause = len(intervals) == 1 and interval_is_None_or_whitespace(intervals[0])
  if is_pause:
    mark = intervals[0].mark
  else:
    mark = intervals_to_text(
      intervals, tier_string_format.get_word_separator(), strip=False)
  interval = Interval(
    minTime=first_interval.minTime,
    maxTime=last_interval.maxTime,
    mark=mark,
  )
  return interval
