from logging import getLogger
from typing import Generator, Iterable, List, Optional, Set

from text_utils import StringFormat, symbols_endswith, symbols_strip
from textgrid.textgrid import Interval, IntervalTier, TextGrid
from textgrid_tools.core.mfa.helper import (check_is_valid_grid,
                                            get_first_tier,
                                            interval_is_None_or_whitespace,
                                            merge_intervals, replace_tier,
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


def join_intervals(grid: TextGrid, tier_name: str, tier_string_format: StringFormat, tier_interval_format: IntervalFormat, strip_symbols: Set[str], punctuation_symbols: Set[str], output_tier_name: Optional[str] = None, overwrite_tier: bool = True) -> None:
  assert can_join_intervals(grid, tier_name, output_tier_name, overwrite_tier)

  if output_tier_name is None:
    output_tier_name = tier_name

  tier = get_first_tier(grid, tier_name)

  new_tier = IntervalTier(
    name=output_tier_name,
    minTime=grid.minTime,
    maxTime=grid.maxTime,
  )

  chunked_intervals = chunk_intervals(
    tier.intervals, tier_string_format, strip_symbols, punctuation_symbols)

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


def chunk_intervals(intervals: Iterable[Interval], intervals_string_format: StringFormat, strip_symbols: Set[str], punctuation_symbols: Set[str]) -> Generator[List[Interval], None, None]:
  current_sentence = []
  for interval in intervals:
    interval_is_pause_between_sentences = len(
      current_sentence) == 0 and interval_is_None_or_whitespace(interval)

    if interval_is_pause_between_sentences:
      yield [interval]
      continue

    current_sentence.append(interval)

    mark = interval.mark
    if mark is None:
      mark = ""

    mark_symbols = intervals_string_format.convert_string_to_symbols(mark)
    mark_symbols_stripped = symbols_strip(mark_symbols, strip=strip_symbols)
    was_ending = symbols_endswith(mark_symbols_stripped, punctuation_symbols)
    if was_ending:
      yield current_sentence
      current_sentence = []
