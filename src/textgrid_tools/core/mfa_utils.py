import string
from functools import partial
from logging import getLogger
from typing import Dict, List, Set, Tuple, cast

import numpy as np
from audio_utils.audio import get_duration_s_samples
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
from text_utils.text import symbols_to_words, text_normalize, text_to_sentences
from text_utils.types import Symbol, Symbols
from text_utils.utils import (pronunciation_dict_to_tuple_dict, symbols_strip,
                              symbols_to_upper)
from textgrid.textgrid import Interval, IntervalTier, TextGrid
from textgrid_tools.utils import durations_to_intervals

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


def get_pronunciation_dict_from_texts(texts: List[str], text_format: SymbolFormat, language: Language, trim_symbols: Set[Symbol]) -> PronunciationDict:
  merged_text = " ".join(texts)
  symbols = text_to_symbols(
    lang=language,
    text=merged_text,
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


def extract_sentences_to_textgrid(original_text: str, text_format: SymbolFormat, language: Language, audio: np.ndarray, sr: int, tier_name: str, time_factor: float) -> TextGrid:
  logger = getLogger(__name__)
  sentences = text_to_sentences(
    text=original_text,
    text_format=text_format,
    lang=language,
  )

  logger.info(f"Extracted {len(sentences)} sentences.")
  audio_len_s = get_duration_s_samples(len(audio), sr)
  audio_len_s_streched = audio_len_s * time_factor
  logger.info(f"Streched time by factor {time_factor}: {audio_len_s} -> {audio_len_s_streched}")

  grid = TextGrid(
    minTime=0,
    maxTime=audio_len_s_streched,
    name=None,
    strict=True,
  )

  tier = IntervalTier(
    name=tier_name,
    minTime=grid.minTime,
    maxTime=grid.maxTime,
  )

  avg_character_len_s = audio_len_s_streched / len(original_text)
  durations: List[Tuple[str, float]] = []
  for sentence in sentences:
    sentence_duration = len(sentence) * avg_character_len_s
    durations.append((sentence, sentence_duration))

  intervals = durations_to_intervals(durations, maxTime=grid.maxTime)
  tier.intervals.extend(intervals)
  grid.append(tier)

  return grid


def merge_words_together(grid: TextGrid, reference_tier_name: str, new_tier_name: str, min_pause_s: float) -> TextGrid:
  logger = getLogger(__name__)

  new_grid = TextGrid(
    minTime=grid.minTime,
    maxTime=grid.maxTime,
    name=grid.name,
    strict=grid.strict,
  )

  tier = IntervalTier(
    name=new_tier_name,
    minTime=new_grid.minTime,
    maxTime=new_grid.maxTime,
  )

  reference_tier = cast(IntervalTier, grid.getFirst(reference_tier_name))

  durations: List[Tuple[str, float]] = []
  current_batch = []
  current_duration = 0
  interval: Interval
  for interval in reference_tier.intervals:
    is_empty = interval_is_empty(interval)
    if is_empty:
      if interval.duration() < min_pause_s:
        current_duration += interval.duration()
      else:
        if len(current_batch) > 0:
          batch_str = " ".join(current_batch)
          durations.append((batch_str, current_duration))
          current_batch.clear()
          current_duration = 0
        durations.append((interval.mark, interval.duration()))
    else:
      current_batch.append(interval.mark)
      current_duration += interval.duration()

  if len(current_batch) > 0:
    batch_str = " ".join(current_batch)
    durations.append((batch_str, current_duration))

  intervals = durations_to_intervals(durations, maxTime=new_grid.maxTime)
  tier.intervals.extend(intervals)
  new_grid.append(tier)

  return new_grid


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


def convert_original_text_to_phonemes(text_format: SymbolFormat, language: Language, grid: TextGrid, original_text_tier_name: str, new_arpa_tier_name: str, new_ipa_tier_name: str, pronunciation_dict: PronunciationDict, overwrite_existing_tiers: bool, trim_symbols: Set[Symbol]):
  logger = getLogger(__name__)

  original_text_tier: IntervalTier = grid.getFirst(original_text_tier_name)
  if original_text_tier is None:
    raise Exception("Original text-tier not found!")

  new_ipa_tier: IntervalTier = grid.getFirst(new_ipa_tier_name)
  if new_ipa_tier is not None and not overwrite_existing_tiers:
    raise Exception("IPA tier already exists!")

  new_arpa_tier = grid.getFirst(new_arpa_tier_name)
  if new_arpa_tier is not None and not overwrite_existing_tiers:
    raise Exception("ARPA tier already exists!")

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

  words_arpa = symbols_to_words(symbols_arpa)

  original_text_tier_intervals: List[Interval] = original_text_tier.intervals

  new_arpa_tier = IntervalTier(
    minTime=original_text_tier.minTime,
    maxTime=original_text_tier.maxTime,
    name=new_arpa_tier_name,
  )

  new_ipa_tier = IntervalTier(
    minTime=original_text_tier.minTime,
    maxTime=original_text_tier.maxTime,
    name=new_ipa_tier_name,
  )

  for interval in original_text_tier_intervals:
    new_ipa = ""
    new_arpa = ""

    if not interval_is_empty(interval):
      new_arpa_tuple = words_arpa.pop(0)
      new_arpa = " ".join(new_arpa_tuple)

      new_ipa_tuple = symbols_map_arpa_to_ipa(
        arpa_symbols=new_arpa_tuple,
        ignore={},
        replace_unknown=False,
        replace_unknown_with=None,
      )

      new_ipa = "".join(new_ipa_tuple)
      logger.debug(f"Assigned \"{new_arpa}\" & \"{new_ipa}\" to \"{interval.mark}\".")

    new_arpa_interval = Interval(
      minTime=interval.minTime,
      maxTime=interval.maxTime,
      mark=new_arpa,
    )

    new_arpa_tier.addInterval(new_arpa_interval)

    new_ipa_interval = Interval(
      minTime=interval.minTime,
      maxTime=interval.maxTime,
      mark=new_ipa,
    )

    new_ipa_tier.addInterval(new_ipa_interval)

  grid.append(new_arpa_tier)
  grid.append(new_ipa_tier)


def add_phoneme_layer_containing_punctuation(text_format: SymbolFormat, language: Language, grid: TextGrid, original_text_tier_name: str, reference_tier_name: str, new_ipa_tier_name: str, new_arpa_tier_name: str, pronunciation_dict: PronunciationDict, overwrite_existing_tiers: bool, trim_symbols: Set[Symbol]):
  logger = getLogger(__name__)

  original_text_tier: IntervalTier = grid.getFirst(original_text_tier_name)
  if original_text_tier is None:
    raise Exception("Original text-tier not found!")

  reference_tier: IntervalTier = grid.getFirst(reference_tier_name)
  if reference_tier is None:
    raise Exception("Reference-tier not found!")

  new_ipa_tier: IntervalTier = grid.getFirst(new_ipa_tier_name)
  if new_ipa_tier is not None and not overwrite_existing_tiers:
    raise Exception("IPA tier already exists!")

  new_arpa_tier = grid.getFirst(new_arpa_tier_name)
  if new_arpa_tier is not None and not overwrite_existing_tiers:
    raise Exception("ARPA tier already exists!")

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

  dont_merge = trim_symbols | set(string.whitespace)
  merge_symbols = trim_symbols | {"-"}  # DEFAULT_IGNORE_PUNCTUATION | set("-"),

  final_arpa_symbols = symbols_arpa

  final_arpa_symbols = merge_right(
    symbols=final_arpa_symbols,
    ignore_merge_symbols=dont_merge,
    merge_symbols=merge_symbols,
  )

  final_arpa_symbols = merge_left(
    symbols=final_arpa_symbols,
    ignore_merge_symbols=dont_merge,
    merge_symbols=merge_symbols,
  )

  final_arpa_symbols = [symbol for symbol in final_arpa_symbols if symbol != " "]

  final_ipa_symbols = symbols_ipa

  final_ipa_symbols = merge_right(
    symbols=final_ipa_symbols,
    ignore_merge_symbols=dont_merge,
    merge_symbols=merge_symbols,
  )

  final_ipa_symbols = merge_left(
    symbols=final_ipa_symbols,
    ignore_merge_symbols=dont_merge,
    merge_symbols=merge_symbols,
  )

  final_ipa_symbols = [symbol for symbol in final_ipa_symbols if symbol != " "]

  #logger.debug(f"Old symbols: {tier_to_text(reference_tier, join_with='')}")
  #logger.debug(f"New symbols: \"{''.join(final_ipa_symbols)}\" // \"{' '.join(final_arpa_symbols)}\"")

  intervals: List[Interval] = reference_tier.intervals
  new_arpa_tier = IntervalTier(
    minTime=reference_tier.minTime,
    maxTime=reference_tier.maxTime,
    name=new_arpa_tier_name,
  )

  new_ipa_tier = IntervalTier(
    minTime=reference_tier.minTime,
    maxTime=reference_tier.maxTime,
    name=new_ipa_tier_name,
  )

  for interval in intervals:
    new_ipa_symbol = ""
    new_arpa_symbol = ""

    if not interval_is_empty(interval):
      new_ipa_symbol = final_ipa_symbols.pop(0)
      new_arpa_symbol = final_arpa_symbols.pop(0)

      logger.debug(f"Assigned \"{new_arpa_symbol}\" & \"{new_ipa_symbol}\" to \"{interval.mark}\".")

    new_arpa_interval = Interval(
      minTime=interval.minTime,
      maxTime=interval.maxTime,
      mark=new_arpa_symbol,
    )

    new_arpa_tier.addInterval(new_arpa_interval)

    new_ipa_interval = Interval(
      minTime=interval.minTime,
      maxTime=interval.maxTime,
      mark=new_ipa_symbol,
    )

    new_ipa_tier.addInterval(new_ipa_interval)

  grid.append(new_arpa_tier)
  grid.append(new_ipa_tier)
