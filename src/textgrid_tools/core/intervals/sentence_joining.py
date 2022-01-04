from logging import getLogger
from typing import Generator, Iterable, Iterator, Optional, Set, Tuple

from text_utils import SYMBOLS_SEPARATOR, StringFormat
from text_utils.utils import symbols_strip
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


def join_intervals(grid: TextGrid, tier_name: str, tier_string_format: StringFormat, tier_interval_format: IntervalFormat, strip_symbols: Set[str], punctuation_symbols: Set[str], output_tier_name: Optional[str] = None, overwrite_tier: bool = True) -> None:
  assert can_join_intervals(grid, tier_name, output_tier_name, overwrite_tier)

  if output_tier_name is None:
    output_tier_name = tier_name

  tier = get_first_tier(grid, tier_name)

  interval_iterator: Iterator[Interval] = None

  interval_iterator = join_via_sentences(
    tier, tier_string_format, tier_interval_format, strip_symbols, punctuation_symbols)

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


def join_via_sentences(tier: IntervalTier, tier_string_format: StringFormat, interval_format: IntervalFormat, strip_symbols: Set[str], punctuation_symbols: Set[str]) -> Generator[Interval, None, None]:
  assert interval_format in {IntervalFormat.WORDS, IntervalFormat.WORD}
  current_sentence = []
  all_sentences = []
  for interval in tier.intervals:
    interval_is_pause_between_sentences = len(
      current_sentence) == 0 and interval_is_None_or_whitespace(interval)

    if interval_is_pause_between_sentences:
      all_sentences.append([interval])
      continue

    current_sentence.append(interval)
    current_interval_tuple = interval_to_tuple(interval, tier_string_format)
    interval_content = symbols_strip(current_interval_tuple, strip={""} | strip_symbols)
    is_ending = symbols_endswith(interval_content, punctuation_symbols)
    if is_ending:
      all_sentences.append(current_sentence)
      current_sentence = []

  for sentence in all_sentences:
    yield merge_intervals(sentence, tier_string_format)


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


def symbols_endswith(symbols: Tuple[str, ...], endswith: Set[str]) -> bool:
  if len(symbols) == 0:
    return False
  last_symbol = symbols[-1]
  result = last_symbol in endswith
  return result


def interval_to_tuple(interval: Interval, string_format: StringFormat) -> Tuple[str, ...]:
  if interval is None:
    return tuple()

  interval_text: str = interval.mark

  if string_format == StringFormat.SYMBOLS:
    result = tuple(interval_text.split(SYMBOLS_SEPARATOR))
  elif string_format == StringFormat.TEXT:
    result = tuple(interval_text)
  else:
    assert False

  return result
