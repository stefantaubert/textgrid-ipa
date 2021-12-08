from logging import getLogger
from typing import List

from pronunciation_dict_parser import PronunciationDict
from text_utils import Language, text_to_symbols
from text_utils.symbol_format import SymbolFormat
from text_utils.text import symbols_to_words
from textgrid.textgrid import Interval, IntervalTier, TextGrid
from textgrid_tools.core.mfa.arpa import SIL
from textgrid_tools.core.mfa.helper import interval_is_empty
from textgrid_tools.utils import update_or_add_tier


def add_layer_containing_original_text(original_text: str, grid: TextGrid, reference_tier_name: str, alignment_dict: PronunciationDict, new_tier_name: str, overwrite_existing_tier: bool) -> None:
  logger = getLogger(__name__)
  reference_tier: IntervalTier = grid.getFirst(reference_tier_name)
  if reference_tier is None:
    raise Exception("Reference-tier not found!")
  new_tier = grid.getFirst(new_tier_name)
  if new_tier is not None and not overwrite_existing_tier:
    raise Exception("Tier already exists!")

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
    logger.info(f"Ignored {ignored_count} \"sil\" annotations.")

  intervals: List[Interval] = reference_tier.intervals
  new_tier = IntervalTier(
    minTime=reference_tier.minTime,
    maxTime=reference_tier.maxTime,
    name=new_tier_name,
  )

  non_empty_intervals = [interval for interval in intervals if not interval_is_empty(interval)]

  if len(non_empty_intervals) != len(words):
    logger.error(f"Couldn't align words -> {len(non_empty_intervals)} vs. {len(words)}!")
    min_len = min(len(non_empty_intervals), len(words))
    for i in range(min_len):
      is_not_same = str(non_empty_intervals[i].mark).lower() != ''.join(words[i]).lower()
      logger.info(
        f"{'===>' if is_not_same else ''} {non_empty_intervals[i].mark} vs. {''.join(words[i])}")
    logger.info("...")
    return

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

    new_tier.addInterval(new_interval)

  if overwrite_existing_tier:
    update_or_add_tier(grid, new_tier)
  else:
    grid.append(new_tier)
  return
