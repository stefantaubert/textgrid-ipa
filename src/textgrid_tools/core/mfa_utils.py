from logging import getLogger
from typing import List

from pronunciation_dict_parser import PronunciationDict, export
from text_utils import (symbols_to_arpa_pronunciation_dict, symbols_to_ipa,
                        text_to_symbols)
from text_utils.language import Language
from text_utils.pronunciation.ipa2symb import (DONT_CHANGE, merge_left,
                                               merge_right)
from text_utils.pronunciation.main import (DEFAULT_IGNORE_PUNCTUATION,
                                           EngToIPAMode, symbols_to_arpa)
from text_utils.symbol_format import SymbolFormat
from text_utils.text import symbols_to_words
from text_utils.utils import symbols_split
from textgrid.textgrid import Interval, IntervalTier, TextGrid


def get_pronunciation_dict(text: str, text_format: SymbolFormat, language: Language) -> PronunciationDict:
  symbols = text_to_symbols(
    lang=language,
    text=text,
    text_format=text_format,
  )
  pronunciation_dict = symbols_to_arpa_pronunciation_dict(
    symbols=symbols,
    consider_annotations=False,
    ignore_case=True,
    language=language,
    split_on_hyphen=True,
    symbols_format=text_format,
  )

  return pronunciation_dict


def add_layer_containing_original_text(original_text: str, text_format: SymbolFormat, language: Language, grid: TextGrid, reference_tier_name: str, new_tier_name: str, overwrite_existing_tier: bool):
  reference_tier: IntervalTier = grid.getFirst(reference_tier_name)
  if reference_tier is None:
    raise Exception("Reference-tier not found!")
  new_tier = grid.getFirst(new_tier_name)
  if new_tier is not None and not overwrite_existing_tier:
    raise Exception("Tier already exists!")

  symbols = text_to_symbols(
    lang=language,
    text=original_text,
    text_format=text_format,
  )

  words = symbols_to_words(symbols)

  intervals: List[Interval] = reference_tier.intervals
  new_tier = IntervalTier(
    minTime=reference_tier.minTime,
    maxTime=reference_tier.maxTime,
    name=new_tier_name,
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

    new_tier.addInterval(new_interval)

  grid.append(new_tier)


def interval_is_empty(interval: Interval) -> bool:
  return interval.mark is None or len(interval.mark.strip()) == 0


def tier_to_text(tier: IntervalTier, join_with: str=" ") -> str:
  words = []
  for interval in tier.intervals:
    if not interval_is_empty(interval):
      interval_text: str = interval.mark
      interval_text = interval_text.strip()
      words.append(interval_text)
  text = join_with.join(words)
  return text


def add_layer_containing_punctuation(text_format: SymbolFormat, language: Language, grid: TextGrid, original_text_tier_name: str, reference_tier_name: str, new_tier_name: str, pronunciation_dict: PronunciationDict, overwrite_existing_tier: bool):
  logger = getLogger(__name__)
  reference_tier: IntervalTier = grid.getFirst(reference_tier_name)
  if reference_tier is None:
    raise Exception("Reference-tier not found!")
  new_tier = grid.getFirst(new_tier_name)
  if new_tier is not None and not overwrite_existing_tier:
    raise Exception("Tier already exists!")

  original_text_tier = grid.getFirst(original_text_tier_name)
  if original_text_tier is None:
    raise Exception("Original text-tier not found!")

  original_text = tier_to_text(original_text_tier)

  symbols = text_to_symbols(
    lang=language,
    text=original_text,
    text_format=text_format,
  )

  symbols_arpa, _ = symbols_to_arpa(
    symbols=symbols,
    consider_annotations=False,
    lang=language,
    symbols_format=text_format,
  )

  final_symbols = symbols_arpa

  final_symbols = merge_right(
    symbols=final_symbols,
    ignore_merge_symbols=DONT_CHANGE,
    merge_symbols=DEFAULT_IGNORE_PUNCTUATION,
  )

  final_symbols = merge_left(
    symbols=final_symbols,
    ignore_merge_symbols=DONT_CHANGE,
    merge_symbols=DEFAULT_IGNORE_PUNCTUATION,
  )

  final_symbols = [symbol for symbol in final_symbols if symbol != " "]

  logger.info(f"Old symbols: {tier_to_text(reference_tier, join_with='')}")
  logger.info(f"New symbols: {''.join(final_symbols)}")

  intervals: List[Interval] = reference_tier.intervals
  new_tier = IntervalTier(
    minTime=reference_tier.minTime,
    maxTime=reference_tier.maxTime,
    name=new_tier_name,
  )
  for interval in intervals:
    new_arpa = ""
    if not interval_is_empty(interval):
      new_arpa_tuple = final_symbols.pop(0)
      new_arpa = ''.join(new_arpa_tuple)
    logger.info(f"Assigned {new_arpa} to {interval.mark}")

    new_interval = Interval(
      minTime=interval.minTime,
      maxTime=interval.maxTime,
      mark=new_arpa,
    )

    new_tier.addInterval(new_interval)

  grid.append(new_tier)
