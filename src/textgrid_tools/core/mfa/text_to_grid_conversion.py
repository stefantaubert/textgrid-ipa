from logging import getLogger
from typing import Optional

from textgrid.textgrid import Interval, IntervalTier, TextGrid
from textgrid_tools.core.mfa.string_format import StringFormat, get_symbols


def can_convert_text_to_grid(tier_out: str, characters_per_second: float) -> bool:
  logger = getLogger(__name__)
  if len(tier_out) == 0:
    logger.error("Please specify an output name!")
    return False

  if characters_per_second <= 0:
    logger.error("characters_per_second need to be > 0!")
    return False
  return True


def get_character_count(text: str, string_format: StringFormat) -> int:
  if string_format == StringFormat.TEXT:
    total_characters = len(text)
    return total_characters

  if string_format == StringFormat.SYMBOLS:
    words = string_format.get_words(text)
    words_symbols = (get_symbols(word) for word in words)
    count_space = max(0, len(words) - 1)
    total_characters = sum(1 for word in words_symbols for symbol in word) + count_space
    return total_characters
  assert False


def convert_text_to_grid(text: str, grid_name_out: Optional[str], tier_out: str, characters_per_second: float, string_format: StringFormat) -> TextGrid:
  assert can_convert_text_to_grid(tier_out, characters_per_second)

  total_characters = get_character_count(text, string_format)

  if total_characters == 0:
    duration = 1
  else:
    duration = total_characters / characters_per_second

  grid = TextGrid(
    maxTime=duration,
    minTime=0,
    name=grid_name_out,
    strict=True,
  )

  tier = IntervalTier(
    name=tier_out,
    minTime=0,
    maxTime=duration,
  )

  interval = Interval(
    minTime=0,
    maxTime=duration,
    mark=text,
  )

  tier.addInterval(interval)
  grid.append(tier)

  return grid
