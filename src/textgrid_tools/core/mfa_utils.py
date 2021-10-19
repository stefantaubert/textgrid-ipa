import string
from functools import partial
from logging import getLogger
from typing import Dict, List, Set

from ordered_set import OrderedSet
from pronunciation_dict_parser import PronunciationDict
from pronunciation_dict_parser.default_parser import (PublicDictType,
                                                      parse_public_dict)
from sentence2pronunciation.core import (get_non_annotated_words,
                                         sentence2pronunciation_cached)
from sentence2pronunciation.lookup_cache import clear_cache
from text_utils import symbols_map_arpa_to_ipa, text_to_symbols
from text_utils.language import Language
from text_utils.pronunciation.ipa2symb import merge_left, merge_right
from text_utils.pronunciation.main import (DEFAULT_IGNORE_PUNCTUATION,
                                           lookup_dict)
from text_utils.symbol_format import SymbolFormat
from text_utils.text import symbols_to_words, text_normalize
from text_utils.types import Symbol, Symbols
from text_utils.utils import (pronunciation_dict_to_tuple_dict, symbols_strip,
                              symbols_to_upper)
from textgrid.textgrid import Interval, IntervalTier, TextGrid

USE_DEFAULT_COMPOUND_MARKER = True  # default compound marker is "-"
DEFAULT_IGNORE_CASE = True


def __lookup_dict_no_oov(word: Symbols, dictionary: Dict[Symbols, Symbols]) -> Symbols:
  word_upper = symbols_to_upper(word)
  if word_upper not in dictionary:
    raise Exception(f"Word {word} pronunciation not found!")

  return dictionary[word_upper][0]


def __eng_to_arpa_no_oov(eng_sentence: Symbols, pronunciations: Dict[Symbols, Symbols], trim_symbols: Set[Symbol]) -> Symbols:
  method = partial(__lookup_dict_no_oov, dictionary=pronunciations)

  result = sentence2pronunciation_cached(
    sentence=eng_sentence,
    annotation_split_symbol=None,
    consider_annotation=False,
    get_pronunciation=method,
    split_on_hyphen=USE_DEFAULT_COMPOUND_MARKER,
    trim_symbols=trim_symbols,
    ignore_case_in_cache=DEFAULT_IGNORE_CASE,
  )

  return result


def interval_is_empty(interval: Interval) -> bool:
  return interval.mark is None or len(interval.mark.strip()) == 0


def tier_to_text(tier: IntervalTier, join_with: str = " ") -> str:
  words = []
  for interval in tier.intervals:
    if not interval_is_empty(interval):
      interval_text: str = interval.mark
      interval_text = interval_text.strip()
      words.append(interval_text)
  text = join_with.join(words)
  return text


def get_pronunciation_dict(text: str, text_format: SymbolFormat, language: Language, trim_symbols: Set[Symbol]) -> PronunciationDict:
  symbols = text_to_symbols(
    lang=language,
    text=text,
    text_format=text_format,
  )

  words = get_non_annotated_words(
    sentence=symbols,
    trim_symbols=trim_symbols,
    consider_annotation=False,
    annotation_split_symbol=None,
    ignore_case=DEFAULT_IGNORE_CASE,
    split_on_hyphen=USE_DEFAULT_COMPOUND_MARKER,
  )

  arpa_dict = parse_public_dict(PublicDictType.LIBRISPEECH_ARPA)
  arpa_dict_tuple_based = pronunciation_dict_to_tuple_dict(arpa_dict)
  pronunciation_dict = {}
  method = partial(lookup_dict, dictionary=arpa_dict_tuple_based)
  for word in words:
    arpa_symbols = sentence2pronunciation_cached(
      sentence=word,
      annotation_split_symbol=None,
      consider_annotation=False,
      get_pronunciation=method,
      split_on_hyphen=USE_DEFAULT_COMPOUND_MARKER,
      trim_symbols=trim_symbols,
      ignore_case_in_cache=DEFAULT_IGNORE_CASE,
    )

    word_str = "".join(word)
    assert word_str not in pronunciation_dict
    pronunciation_dict[word_str] = OrderedSet([arpa_symbols])

  clear_cache()

  return pronunciation_dict


def normalize_text(original_text: str, text_format: SymbolFormat, language: Language) -> str:
  logger = getLogger(__name__)

  original_text = original_text.replace("\n", " ")
  original_text = original_text.replace("\r", "")

  result = text_normalize(
    text=original_text,
    lang=language,
    text_format=text_format,
  )

  return result


def add_layer_containing_original_text(original_text: str, text_format: SymbolFormat, language: Language, grid: TextGrid, reference_tier_name: str, new_tier_name: str, overwrite_existing_tier: bool, trim_symbols: Set[Symbol]) -> None:
  logger = getLogger(__name__)
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
  for word in words:
    # due to whitespace collapsing there should not be any empty words
    assert len(word) > 0

  # remove words containing only trim_symbols including `-` as these were all removed by MFA
  ignore_symbols = trim_symbols | {"-"}
  words = [word for word in words if len(symbols_strip(word, strip=ignore_symbols)) > 0]

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
      logger.info(f"{non_empty_intervals[i].mark} vs. {''.join(words[i])}")
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

  grid.append(new_tier)
  return


def convert_original_text_to_arpa(text_format: SymbolFormat, language: Language, grid: TextGrid, original_text_tier_name: str, new_tier_name: str, pronunciation_dict: PronunciationDict, overwrite_existing_tier: bool, trim_symbols: Set[Symbol]):
  logger = getLogger(__name__)

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

  clear_cache()

  arpa_dict_tuple_based = pronunciation_dict_to_tuple_dict(pronunciation_dict)

  symbols_arpa = __eng_to_arpa_no_oov(
    eng_sentence=symbols,
    pronunciations=arpa_dict_tuple_based,
    trim_symbols=trim_symbols,
  )

  words = symbols_to_words(symbols_arpa)

  original_text_tier_intervals: List[Interval] = original_text_tier.intervals
  new_tier = IntervalTier(
    minTime=original_text_tier.minTime,
    maxTime=original_text_tier.maxTime,
    name=new_tier_name,
  )

  for interval in original_text_tier_intervals:
    new_arpa = ""
    if not interval_is_empty(interval):
      new_arpa_tuple = words.pop(0)
      new_arpa = ' '.join(new_arpa_tuple)
    logger.info(f"Assigned {new_arpa} to {interval.mark}")

    new_interval = Interval(
      minTime=interval.minTime,
      maxTime=interval.maxTime,
      mark=new_arpa,
    )

    new_tier.addInterval(new_interval)

  grid.append(new_tier)


def convert_original_text_to_ipa(text_format: SymbolFormat, language: Language, grid: TextGrid, original_text_tier_name: str, new_tier_name: str, pronunciation_dict: PronunciationDict, overwrite_existing_tier: bool, trim_symbols: Set[Symbol]):
  logger = getLogger(__name__)
  logger.info(f"Trim symbols: {' '.join(sorted(trim_symbols))} (#{len(trim_symbols)})")
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

  arpa_dict_tuple_based = pronunciation_dict_to_tuple_dict(pronunciation_dict)

  symbols_arpa = __eng_to_arpa_no_oov(
    eng_sentence=symbols,
    pronunciations=arpa_dict_tuple_based,
    trim_symbols=trim_symbols,
  )

  clear_cache()

  result_ipa = symbols_map_arpa_to_ipa(
    arpa_symbols=symbols_arpa,
    ignore={},
    replace_unknown=False,
    replace_unknown_with=None,
  )

  words = symbols_to_words(result_ipa)

  original_text_tier_intervals: List[Interval] = original_text_tier.intervals
  new_tier = IntervalTier(
    minTime=original_text_tier.minTime,
    maxTime=original_text_tier.maxTime,
    name=new_tier_name,
  )

  for interval in original_text_tier_intervals:
    new_ipa = ""
    if not interval_is_empty(interval):
      new_ipa_tuple = words.pop(0)
      new_ipa = ''.join(new_ipa_tuple)
    logger.info(f"Assigned {new_ipa} to {interval.mark}")

    new_interval = Interval(
      minTime=interval.minTime,
      maxTime=interval.maxTime,
      mark=new_ipa,
    )

    new_tier.addInterval(new_interval)

  grid.append(new_tier)


def add_ipa_layer_containing_punctuation(text_format: SymbolFormat, language: Language, grid: TextGrid, original_text_tier_name: str, reference_tier_name: str, new_tier_name: str, pronunciation_dict: PronunciationDict, overwrite_existing_tier: bool, trim_symbols: Set[Symbol]):
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

  arpa_dict_tuple_based = pronunciation_dict_to_tuple_dict(pronunciation_dict)

  symbols_arpa = __eng_to_arpa_no_oov(
    eng_sentence=symbols,
    pronunciations=arpa_dict_tuple_based,
    trim_symbols=trim_symbols,
  )

  clear_cache()

  symbols_ipa = symbols_map_arpa_to_ipa(
    arpa_symbols=symbols_arpa,
    ignore=set(),
    replace_unknown=False,
    replace_unknown_with=None,
  )

  final_symbols = symbols_ipa

  dont_merge = trim_symbols | set(string.whitespace)

  final_symbols = merge_right(
    symbols=final_symbols,
    ignore_merge_symbols=dont_merge,
    merge_symbols=trim_symbols | set("-"),
  )

  final_symbols = merge_left(
    symbols=final_symbols,
    ignore_merge_symbols=dont_merge,
    merge_symbols=DEFAULT_IGNORE_PUNCTUATION | set("-"),
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
