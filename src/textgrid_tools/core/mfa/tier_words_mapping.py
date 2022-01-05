from logging import getLogger
from typing import List

from pronunciation_dict_parser import PronunciationDict
from text_utils import Language, text_to_symbols
from text_utils.string_format import StringFormat
from text_utils.symbol_format import SymbolFormat
from text_utils.text import symbols_to_words
from text_utils.utils import symbols_to_lower
from textgrid.textgrid import Interval, IntervalTier, TextGrid
from textgrid_tools.core.mfa.arpa import SIL
from textgrid_tools.core.mfa.helper import (check_is_valid_grid,
                                            get_first_tier,
                                            interval_is_None_or_whitespace,
                                            merge_marks, merge_symbols,
                                            tier_exists, tier_to_text)
from textgrid_tools.core.mfa.interval_format import IntervalFormat
from textgrid_tools.utils import update_or_add_tier


def can_map_words_to_tier(grid: TextGrid, tier: str, reference_grid: TextGrid, reference_tier: str, new_tier: str, overwrite_tier: bool) -> bool:
  logger = getLogger(__name__)

  if not check_is_valid_grid(grid):
    logger.error("Grid is invalid!")
    return False

  if not check_is_valid_grid(reference_grid):
    logger.error("Reference grid is invalid!")
    return False

  if not tier_exists(grid, tier):
    logger.error(f"Tier \"{tier}\" not found!")
    return False

  if not tier_exists(reference_grid, reference_tier):
    logger.error(f"Tier \"{reference_tier}\" not found!")
    return False

  if tier_exists(grid, new_tier) and not overwrite_tier:
    logger.error(f"Tier \"{new_tier}\" already exists!")
    return False

  # todo check alignment

  return True


def map_words_to_tier(grid: TextGrid, tier_name: str, tier_string_format: StringFormat, tier_interval_format: IntervalFormat, reference_grid: TextGrid, reference_tier_name: str, reference_tier_string_format: StringFormat, reference_tier_interval_format: IntervalFormat, new_tier: str, overwrite_tier: bool) -> None:
  logger = getLogger(__name__)
  tier = get_first_tier(grid, tier_name)
  reference_tier = get_first_tier(reference_grid, reference_tier_name)
  reference_symbols = merge_symbols(reference_tier.intervals,
                                    reference_tier_string_format, reference_tier_interval_format)
  # original_text = tier_to_text(reference_tier, join_with=" ")
  # symbols = text_to_symbols(
  #   lang=Language.ENG,
  #   text=original_text,
  #   text_format=SymbolFormat.GRAPHEMES,
  # )

  reference_words = symbols_to_words(reference_symbols)
  for word in reference_words:
    # due to whitespace collapsing there should not be any empty words
    assert len(word) > 0

  # if original was text then: remove words with silence annotations, that have no corresponding interval
  # old_count = len(words)
  # words = [word for word in words if alignment_dict[''.join(word).upper()][0] != (SIL,)]
  # ignored_count = old_count - len(words)
  # if ignored_count > 0:
  #   logger.info(f"Ignored {ignored_count} \"{SIL}\" annotations.")

  tier_symbols = merge_symbols(tier.intervals, tier_string_format, tier_interval_format)
  tier_words = symbols_to_words(tier_symbols)

  if len(reference_words) != len(tier_words):
    logger.error(f"Couldn't align words -> {len(tier_words)} vs. {len(reference_words)}!")
    min_len = min(len(tier_words), len(reference_words))
    for i in range(min_len):
      is_not_same = symbols_to_lower(tier_words[i]) != symbols_to_lower(reference_words[i])

      logger.info(
        f"{'===>' if is_not_same else ''} {''.join(tier_words[i])} vs. {''.join(reference_words[i])}")
    logger.info("...")
    raise Exception()

  res_tier = IntervalTier(
    minTime=tier.minTime,
    maxTime=tier.maxTime,
    name=new_tier,
  )

  intervals: List[Interval] = tier.intervals

  for interval in intervals:
    new_word = ""
    if not interval_is_None_or_whitespace(interval):
      new_word_symbols = reference_words.pop(0)
      new_word = tier_string_format.convert_symbols_to_string(new_word_symbols)

    new_interval = Interval(
      minTime=interval.minTime,
      maxTime=interval.maxTime,
      mark=new_word,
    )
    res_tier.addInterval(new_interval)

  if overwrite_tier:
    update_or_add_tier(grid, res_tier)
  else:
    grid.append(res_tier)
