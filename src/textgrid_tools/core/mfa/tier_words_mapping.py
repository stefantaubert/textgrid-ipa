from logging import getLogger
from typing import List

from pronunciation_dict_parser import PronunciationDict
from text_utils import Language, text_to_symbols
from text_utils.symbol_format import SymbolFormat
from text_utils.text import symbols_to_words
from textgrid.textgrid import Interval, IntervalTier, TextGrid
from textgrid_tools.core.mfa.arpa import SIL
from textgrid_tools.core.mfa.helper import (check_is_valid_grid,
                                            get_first_tier, interval_is_empty,
                                            tier_exists, tier_to_text)
from textgrid_tools.utils import update_or_add_tier


def can_map_words_to_tier(grid: TextGrid, tier: str, reference_grid: TextGrid, reference_tier: str, alignment_dict: PronunciationDict, new_tier: str, overwrite_tier: bool) -> bool:
  logger = getLogger(__name__)

  if not check_is_valid_grid(grid):
    logger.error("Grid is invalid!")
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


def map_words_to_tier(grid: TextGrid, tier: str, reference_grid: TextGrid, reference_tier: str, alignment_dict: PronunciationDict, new_tier: str, overwrite_tier: bool) -> None:
  logger = getLogger(__name__)
  tier = get_first_tier(grid, tier)
  reference_tier = get_first_tier(reference_grid, reference_tier)
  original_text = tier_to_text(reference_tier, join_with=" ")
  symbols = text_to_symbols(
    lang=Language.ENG,
    text=original_text,
    text_format=SymbolFormat.GRAPHEMES,
  )

  words = symbols_to_words(symbols)
  for word in words:
    # due to whitespace collapsing there should not be any empty words
    assert len(word) > 0

  # remove words with silence annotations, that have no corresponding interval
  old_count = len(words)
  words = [word for word in words if alignment_dict[''.join(word).upper()][0] != (SIL,)]
  ignored_count = old_count - len(words)
  if ignored_count > 0:
    logger.info(f"Ignored {ignored_count} \"{SIL}\" annotations.")

  intervals: List[Interval] = reference_tier.intervals
  non_empty_intervals = [interval for interval in intervals if not interval_is_empty(interval)]

  if len(non_empty_intervals) != len(words):
    logger.error(f"Couldn't align words -> {len(non_empty_intervals)} vs. {len(words)}!")
    min_len = min(len(non_empty_intervals), len(words))
    for i in range(min_len):
      is_not_same = str(non_empty_intervals[i].mark).lower() != ''.join(words[i]).lower()
      logger.info(
        f"{'===>' if is_not_same else ''} {non_empty_intervals[i].mark} vs. {''.join(words[i])}")
    logger.info("...")
    raise Exception()

  res_tier = IntervalTier(
    minTime=reference_tier.minTime,
    maxTime=reference_tier.maxTime,
    name=new_tier,
  )

  for interval in intervals:
    new_word = ""
    if not interval_is_empty(interval):
      new_word_tuple = words.pop(0)
      new_word = ''.join(new_word_tuple)

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
