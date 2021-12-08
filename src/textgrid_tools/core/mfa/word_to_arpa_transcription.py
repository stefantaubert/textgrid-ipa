import re
from logging import getLogger
from typing import List, Set

from sentence2pronunciation import (LookupCache,
                                    sentences2pronunciations_from_cache_mp)
from text_utils import Language, text_to_symbols
from text_utils.pronunciation.ipa2symb import merge_left, merge_right
from text_utils.symbol_format import SymbolFormat
from text_utils.text import symbols_to_words, words_to_symbols
from text_utils.types import Symbol
from textgrid.textgrid import Interval, IntervalTier, TextGrid
from textgrid_tools.core.mfa.helper import interval_is_empty, tier_to_text
from textgrid_tools.utils import update_or_add_tier


def transcribe_words_to_arpa(grid: TextGrid, original_text_tier_name: str, tier_name: str, consider_annotations: bool, ignore_case: bool, cache: LookupCache, overwrite_existing_tier: bool):
  logger = getLogger(__name__)

  original_text_tier: IntervalTier = grid.getFirst(original_text_tier_name)
  if original_text_tier is None:
    raise Exception("Original text-tier not found!")

  if grid.getFirst(tier_name) is not None and not overwrite_existing_tier:
    raise Exception("ARPA tier already exists!")

  original_text = tier_to_text(original_text_tier)

  symbols = text_to_symbols(
    lang=Language.ENG,
    text=original_text,
    text_format=SymbolFormat.GRAPHEMES,
  )

  symbols_arpa = sentences2pronunciations_from_cache_mp(
    cache=cache,
    sentences={symbols},
    annotation_split_symbol="/",
    chunksize=1,
    consider_annotation=consider_annotations,
    ignore_case=ignore_case,
    n_jobs=1,
  )[symbols]

  words_arpa_with_punctuation = symbols_to_words(symbols_arpa)

  original_text_tier_intervals: List[Interval] = original_text_tier.intervals

  new_arpa_tier = IntervalTier(
    minTime=original_text_tier.minTime,
    maxTime=original_text_tier.maxTime,
    name=tier_name,
  )

  for interval in original_text_tier_intervals:
    new_arpa = ""

    if not interval_is_empty(interval):
      interval_contains_space = " " in interval.mark
      if interval_contains_space:
        logger.error(
          f"Invalid interval mark: \"{interval.mark}\" on [{interval.minTime}, {interval.maxTime}]!")
        # raise Exception()
      new_arpa_tuple = words_arpa_with_punctuation.pop(0)
      # if new_arpa_tuple == (SIL,):
      #  logger.info(f"Skip {interval.mark} as it is only sil.")
      #  continue
      new_arpa = " ".join(new_arpa_tuple)
      logger.debug(f"Assigned \"{new_arpa}\" to \"{interval.mark}\".")

    new_arpa_interval = Interval(
      minTime=interval.minTime,
      maxTime=interval.maxTime,
      mark=new_arpa,
    )

    new_arpa_tier.addInterval(new_arpa_interval)

  if overwrite_existing_tier:
    update_or_add_tier(grid, new_arpa_tier)
  else:
    grid.append(new_arpa_tier)


def transcribe_words_to_arpa_on_phoneme_level(grid: TextGrid, words_tier_name: str, phoneme_tier_name: str, arpa_tier_name: str, consider_annotations: bool, ignore_case: bool, cache: LookupCache, overwrite_existing_tier: bool, trim_symbols: Set[Symbol]):
  logger = getLogger(__name__)

  word_tier: IntervalTier = grid.getFirst(words_tier_name)
  if word_tier is None:
    raise Exception("Word tier not found!")

  phoneme_tier: IntervalTier = grid.getFirst(phoneme_tier_name)
  if phoneme_tier is None:
    raise Exception("Phoneme tier not found!")

  if grid.getFirst(arpa_tier_name) is not None and not overwrite_existing_tier:
    raise Exception("ARPA tier already exists!")

  original_text = tier_to_text(word_tier)

  symbols = text_to_symbols(
    lang=Language.ENG,
    text=original_text,
    text_format=SymbolFormat.GRAPHEMES,
  )

  symbols_arpa = sentences2pronunciations_from_cache_mp(
    cache=cache,
    sentences={symbols},
    annotation_split_symbol="/",
    chunksize=1,
    consider_annotation=consider_annotations,
    ignore_case=ignore_case,
    n_jobs=1,
  )[symbols]

  words_arpa_with_punctuation = symbols_to_words(symbols_arpa)

  replace_str = re.escape(''.join(trim_symbols))
  pattern = re.compile(rf"[{replace_str}]+")
  # remove words consisting only of punctuation since these were annotated as silence
  words_arpa_with_punctuation = [word for word in words_arpa_with_punctuation if len(
    re.sub(pattern, "", ''.join(word))) > 0]
  symbols_arpa = words_to_symbols(words_arpa_with_punctuation)

  dont_merge = {" "}

  final_arpa_symbols = symbols_arpa

  final_arpa_symbols = merge_right(
    symbols=final_arpa_symbols,
    ignore_merge_symbols=dont_merge,
    merge_symbols=trim_symbols,
    insert_symbol=" ",
  )

  final_arpa_symbols = merge_left(
    symbols=final_arpa_symbols,
    ignore_merge_symbols=dont_merge,
    merge_symbols=trim_symbols,
    insert_symbol=" ",
  )

  final_arpa_symbols = [symbol for symbol in final_arpa_symbols if symbol != " "]

  reference_tier_intervals: List[Interval] = phoneme_tier.intervals
  new_tier = IntervalTier(
    minTime=phoneme_tier.minTime,
    maxTime=phoneme_tier.maxTime,
    name=arpa_tier_name,
  )

  for interval in reference_tier_intervals:
    new_arpa_symbol = ""

    if not interval_is_empty(interval):
      new_arpa_symbol = final_arpa_symbols.pop(0)
      logger.debug(f"Assigned \"{new_arpa_symbol}\" to \"{interval.mark}\".")

    new_arpa_interval = Interval(
      minTime=interval.minTime,
      maxTime=interval.maxTime,
      mark=new_arpa_symbol,
    )

    new_tier.addInterval(new_arpa_interval)

  if overwrite_existing_tier:
    update_or_add_tier(grid, new_tier)
  else:
    grid.append(new_tier)
