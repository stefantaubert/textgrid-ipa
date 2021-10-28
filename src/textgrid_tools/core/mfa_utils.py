import re
import string
from collections import OrderedDict
from functools import partial
from logging import getLogger
from multiprocessing import cpu_count
from typing import Dict, List, Optional, Set, Tuple, cast

import numpy as np
from audio_utils.audio import get_duration_s_samples
from ordered_set import OrderedSet
from pronunciation_dict_parser import PronunciationDict
from pronunciation_dict_parser.default_parser import (PublicDictType,
                                                      parse_public_dict)
from sentence2pronunciation.core import (
    get_non_annotated_words, prepare_cache_mp, sentence2pronunciation_cached,
    sentences2pronunciations_from_cache_mp)
from sentence2pronunciation.lookup_cache import LookupCache
from text_utils import (symbols_map_arpa_to_ipa,
                        symbols_remove_non_arpa_symbols, text_to_symbols)
from text_utils.language import Language
from text_utils.pronunciation.arpa_symbols import (ALL_ARPA_INCL_STRESSES,
                                                   CONSONANTS, STRESS_NONE,
                                                   STRESS_PRIMARY,
                                                   STRESS_SECONDARY, VOWELS, H)
from text_utils.pronunciation.ipa2symb import (merge_left, merge_right,
                                               merge_together)
from text_utils.pronunciation.main import (DEFAULT_IGNORE_PUNCTUATION,
                                           get_eng_to_arpa_lookup_method,
                                           lookup_dict)
from text_utils.pronunciation.pronunciation_dict_cache import \
    get_eng_pronunciation_dict_arpa
from text_utils.symbol_format import SymbolFormat
from text_utils.text import (symbols_to_words, text_normalize,
                             text_to_sentences, words_to_symbols)
from text_utils.types import Symbol, Symbols
from text_utils.utils import (pronunciation_dict_to_tuple_dict,
                              split_symbols_on, symbols_ignore, symbols_join,
                              symbols_split, symbols_strip, symbols_to_lower,
                              symbols_to_upper)
from textgrid.textgrid import Interval, IntervalTier, TextGrid
from textgrid_tools.utils import durations_to_intervals, update_or_add_tier
from tqdm import tqdm

USE_DEFAULT_COMPOUND_MARKER = True  # default compound marker is "-"
DEFAULT_IGNORE_CASE = True
ALLOWED_MFA_MODEL_SYMBOLS = {
  'AA0',
  'AA1',
  'AA2',
  'AE0',
  'AE1',
  'AE2',
  'AH0',
  'AH1',
  'AH2',
  'AO0',
  'AO1',
  'AO2',
  'AW0',
  'AW1',
  'AW2',
  'AY0',
  'AY1',
  'AY2',
  'B',
  'CH',
  'D',
  'DH',
  'EH0',
  'EH1',
  'EH2',
  'ER0',
  'ER1',
  'ER2',
  'EY0',
  'EY1',
  'EY2',
  'F',
  'G',
  'HH',
  'IH0',
  'IH1',
  'IH2',
  'IY0',
  'IY1',
  'IY2',
  'JH',
  'K',
  'L',
  'M',
  'N',
  'NG',
  'OW0',
  'OW1',
  'OW2',
  'OY0',
  'OY1',
  'OY2',
  'P',
  'R',
  'S',
  'SH',
  'T',
  'TH',
  'UH0',
  'UH1',
  'UH2',
  'UW0',
  'UW1',
  'UW2',
  'V',
  'W',
  'Y',
  'Z',
  'ZH',
}

# # MFA has no symbols which are not in ALL_ARPA_INCL_STRESSES
# print(ALLOWED_MFA_MODEL_SYMBOLS.difference(ALL_ARPA_INCL_STRESSES))
# # Some are not included in MFA
# x = '\n'.join(sorted((ALL_ARPA_INCL_STRESSES - VOWELS).difference(ALLOWED_MFA_MODEL_SYMBOLS)))
# print(f"Not included:\n{x}")


def __lookup_dict_no_oov(word: Symbols, dictionary: Dict[Symbols, Symbols]) -> Symbols:
  word_upper = symbols_to_upper(word)
  if word_upper not in dictionary:
    raise Exception(f"Word {word} pronunciation not found!")

  return dictionary[word_upper][0]


def __eng_to_arpa_no_oov(eng_sentence: Symbols, pronunciations: Dict[Symbols, Symbols]) -> Symbols:
  method = partial(__lookup_dict_no_oov, dictionary=pronunciations)

  result = sentence2pronunciation_cached(
    sentence=eng_sentence,
    annotation_split_symbol=None,
    consider_annotation=False,
    get_pronunciation=method,
    split_on_hyphen=False,
    trim_symbols={},
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


def get_pronunciation_dict(text: str, text_format: SymbolFormat, language: Language, trim_symbols: Set[Symbol], dict_type: PublicDictType) -> PronunciationDict:
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

  arpa_dict = parse_public_dict(dict_type)
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


def normalize_text(original_text: str) -> str:
  logger = getLogger(__name__)

  original_text = original_text.replace("\n", " ")
  original_text = original_text.replace("\r", "")

  result = text_normalize(
    text=original_text,
    lang=Language.ENG,
    text_format=SymbolFormat.GRAPHEMES,
  )

  return result


def remove_tiers(grids: List[TextGrid], tier_name: str) -> None:
  logger = getLogger(__name__)

  for grid in grids:
    remove_tier(grid, tier_name)


def remove_tier(grid: TextGrid, tier_name: str) -> None:
  logger = getLogger(__name__)

  tier: IntervalTier = grid.getFirst(tier_name)
  if tier is None:
    logger.exception("Tier not found!")
    raise Exception()

  grid.tiers.remove(tier)


MAX_THREAD_COUNT = cpu_count() - 1


def get_arpa_pronunciation_dicts_from_texts(texts: List[str], trim_symbols: Set[Symbol], dict_type: PublicDictType, consider_annotations: bool) -> Tuple[PronunciationDict, PronunciationDict, LookupCache]:
  logger = getLogger(__name__)
  logger.info(f"Chosen dictionary type: {dict_type}")
  logger.info(f"Getting all sentences...")
  text_sentences = {
    text_to_symbols(
      lang=Language.ENG,
      text=sentence,
      text_format=SymbolFormat.GRAPHEMES,
    )
    for text in tqdm(texts)
    for sentence in text_to_sentences(
      text=text,
      text_format=SymbolFormat.GRAPHEMES,
      lang=Language.ENG
    )
  }

  logger.info(f"Done. Retrieved {len(text_sentences)} unique sentences.")

  logger.info(f"Converting all words to ARPA...")
  cache = prepare_cache_mp(
    sentences=text_sentences,
    annotation_split_symbol="/",
    chunksize=500,
    consider_annotation=consider_annotations,
    get_pronunciation=get_eng_to_arpa_lookup_method(),
    ignore_case=DEFAULT_IGNORE_CASE,
    n_jobs=MAX_THREAD_COUNT,
    split_on_hyphen=USE_DEFAULT_COMPOUND_MARKER,
    trim_symbols=trim_symbols,
  )
  logger.info(f"Done.")

  logger.info(f"Creating pronunciation dictionary...")
  pronunciation_dict_no_punctuation = OrderedDict()
  pronunciation_dict_punctuation = OrderedDict()

  allowed_symbols = ALLOWED_MFA_MODEL_SYMBOLS | {"sil", "spn"}
  for unique_word, arpa_symbols in tqdm(sorted(cache.items())):
    assert len(unique_word) > 0
    assert len(arpa_symbols) > 0

    word_str = "".join(unique_word)
    assert word_str not in pronunciation_dict_punctuation
    # maybe ignore spn here
    pronunciation_dict_punctuation[word_str] = OrderedSet([arpa_symbols])

    arpa_symbols_no_punctuation = symbols_ignore(arpa_symbols, trim_symbols)
    not_allowed_symbols = {
      symbol for symbol in arpa_symbols_no_punctuation if symbol not in allowed_symbols}
    if len(not_allowed_symbols) > 0:
      logger.error(
        "Not all symbols can be aligned! You have missed some trim_symbols or annotated non existent ARPA symbols!")
      logger.info(
        f"Word containing not allowed symbols: {' '.join(sorted(not_allowed_symbols))} ({word_str})")

    arpa_contains_only_punctuation = len(arpa_symbols_no_punctuation) == 0
    if arpa_contains_only_punctuation:
      logger.info(
        f"The arpa of the word {''.join(unique_word)} contains only punctuation, therefore annotating \'sil\'.")
      arpa_symbols_no_punctuation = ("sil",)
    assert word_str not in pronunciation_dict_no_punctuation
    pronunciation_dict_no_punctuation[word_str] = OrderedSet([arpa_symbols_no_punctuation])
  logger.info(f"Done.")
  return pronunciation_dict_no_punctuation, pronunciation_dict_punctuation, cache

  # symbols = text_to_symbols(
  #   lang=Language.ENG,
  #   text=merged_text,
  #   text_format=SymbolFormat.GRAPHEMES,
  # )

  # symbols_lower = symbols_to_lower(symbols)
  # unique_words = set(symbols_to_words(symbols_lower))
  # unique_words -= {""}
  # # else:
  # #   words = get_non_annotated_words(
  # #     sentence=symbols,
  # #     trim_symbols=trim_symbols,
  # #     consider_annotation=False,
  # #     annotation_split_symbol=None,
  # #     ignore_case=DEFAULT_IGNORE_CASE,
  # #     split_on_hyphen=USE_DEFAULT_COMPOUND_MARKER,
  # #   )

  # arpa_dict = parse_public_dict(dict_type)
  # arpa_dict_tuple_based = pronunciation_dict_to_tuple_dict(arpa_dict)
  # pronunciation_dict_no_punctuation = OrderedDict()
  # pronunciation_dict_punctuation = OrderedDict()
  # method = partial(lookup_dict, dictionary=arpa_dict_tuple_based)
  # for unique_word in sorted(unique_words):
  #   assert len(unique_word) > 0
  #   arpa_symbols = sentence2pronunciation_cached(
  #     sentence=unique_word,
  #     annotation_split_symbol=None,
  #     consider_annotation=False,
  #     get_pronunciation=method,
  #     split_on_hyphen=USE_DEFAULT_COMPOUND_MARKER,
  #     trim_symbols=trim_symbols,
  #     ignore_case_in_cache=DEFAULT_IGNORE_CASE,
  #   )

  #   assert len(arpa_symbols) > 0
  #   word_str = "".join(unique_word)
  #   assert word_str not in pronunciation_dict_punctuation
  #   pronunciation_dict_punctuation[word_str] = OrderedSet([arpa_symbols])

  #   arpa_symbols_no_punctuation = symbols_remove_non_arpa_symbols(arpa_symbols)
  #   arpa_contains_only_punctuation = len(arpa_symbols_no_punctuation) == 0
  #   if arpa_contains_only_punctuation:
  #     logger.info(
  #       f"The arpa of the word {''.join(unique_word)} contains only punctuation, therefore annotating \'sil\'.")
  #     arpa_symbols_no_punctuation = ("sil",)
  #   assert word_str not in pronunciation_dict_no_punctuation
  #   pronunciation_dict_no_punctuation[word_str] = OrderedSet([arpa_symbols_no_punctuation])

  # return pronunciation_dict_no_punctuation, pronunciation_dict_punctuation


def extract_sentences_to_textgrid(original_text: str, audio: np.ndarray, sr: int, tier_name: str, time_factor: float) -> TextGrid:
  logger = getLogger(__name__)
  sentences = text_to_sentences(
    text=original_text,
    text_format=SymbolFormat.GRAPHEMES,
    lang=Language.ENG,
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


def extract_tier_to_text(grid: TextGrid, tier_name: str) -> str:
  logger = getLogger(__name__)

  tier: IntervalTier = grid.getFirst(tier_name)
  if tier is None:
    logger.exception("Tier not found!")
    raise Exception()

  result = tier_to_text(tier, join_with=" ")
  return result


def merge_words_together(grid: TextGrid, reference_tier_name: str, new_tier_name: str, min_pause_s: float, overwrite_existing_tier: bool) -> None:
  logger = getLogger(__name__)

  new_tier = grid.getFirst(new_tier_name)
  if new_tier is not None and not overwrite_existing_tier:
    logger.error("Tier already exists!")
    return

  new_tier = IntervalTier(
    name=new_tier_name,
    minTime=grid.minTime,
    maxTime=grid.maxTime,
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

  intervals = durations_to_intervals(durations, maxTime=grid.maxTime)
  new_tier.intervals.extend(intervals)

  grid.append(new_tier)

  if overwrite_existing_tier:
    update_or_add_tier(grid, new_tier)
  else:
    grid.append(new_tier)
  return


def add_layer_containing_original_text(original_text: str, grid: TextGrid, reference_tier_name: str, new_tier_name: str, overwrite_existing_tier: bool) -> None:
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

  # remove words containing only trim_symbols including `-` as these were all removed by MFA
  #ignore_symbols = trim_symbols | {"-"}
  #words = [word for word in words if len(symbols_strip(word, strip=ignore_symbols)) > 0]

  # remove words with silence annotations, that have no corresponding interval
  # words = [word for word in words if len(symbols_strip(word, strip=trim_symbols)) > 0]

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

  if overwrite_existing_tier:
    update_or_add_tier(grid, new_tier)
  else:
    grid.append(new_tier)
  return


def add_graphemes_from_words(grid: TextGrid, original_text_tier_name: str, new_tier_name: str, overwrite_existing_tier: bool):
  logger = getLogger(__name__)
  original_text_tier: IntervalTier = grid.getFirst(original_text_tier_name)
  if original_text_tier is None:
    raise Exception("Original text-tier not found!")

  new_ipa_tier: IntervalTier = grid.getFirst(new_tier_name)
  if new_ipa_tier is not None and not overwrite_existing_tier:
    raise Exception("Graphemes tier already exists!")

  original_text_tier_intervals: List[Interval] = original_text_tier.intervals

  graphemes_tier = IntervalTier(
    minTime=original_text_tier.minTime,
    maxTime=original_text_tier.maxTime,
    name=new_tier_name,
  )

  for interval in original_text_tier_intervals:
    graphemes = ""

    if not interval_is_empty(interval):
      graphemes = " ".join(list(str(interval.mark)))

    graphemes_interval = Interval(
      minTime=interval.minTime,
      maxTime=interval.maxTime,
      mark=graphemes,
    )

    graphemes_tier.addInterval(graphemes_interval)

  if overwrite_existing_tier:
    update_or_add_tier(grid, graphemes_tier)
  else:
    grid.append(graphemes_tier)


def map_arpa_to_ipa_grids(grids: List[TextGrid], arpa_tier_name: str, ipa_tier_name: str, overwrite_existing_tier: bool) -> None:
  for grid in grids:
    map_arpa_to_ipa(grid, arpa_tier_name, ipa_tier_name, overwrite_existing_tier)


def map_arpa_to_ipa(grid: TextGrid, arpa_tier_name: str, ipa_tier_name: str, overwrite_existing_tier: bool):
  logger = getLogger(__name__)

  arpa_tier: IntervalTier = grid.getFirst(arpa_tier_name)
  if arpa_tier is None:
    raise Exception("ARPA tier not found!")

  if grid.getFirst(ipa_tier_name) is not None and not overwrite_existing_tier:
    raise Exception("IPA tier already exists!")

  ipa_tier = IntervalTier(
    minTime=arpa_tier.minTime,
    maxTime=arpa_tier.maxTime,
    name=ipa_tier_name,
  )

  for interval in arpa_tier.intervals:
    arpa_str = cast(str, interval.mark)
    arpa_symbols = tuple(arpa_str.split(" "))
    new_ipa_tuple = symbols_map_arpa_to_ipa(
      arpa_symbols=arpa_symbols,
      ignore={},
      replace_unknown=False,
      replace_unknown_with=None,
    )

    new_ipa = " ".join(new_ipa_tuple)
    logger.debug(f"Mapped \"{arpa_str}\" to \"{new_ipa}\".")

    ipa_interval = Interval(
      minTime=interval.minTime,
      maxTime=interval.maxTime,
      mark=new_ipa,
    )
    ipa_tier.intervals.append(ipa_interval)

  if overwrite_existing_tier:
    update_or_add_tier(grid, ipa_tier)
  else:
    grid.append(ipa_tier)


def transcribe_words_to_arpa(grid: TextGrid, original_text_tier_name: str, tier_name: str, consider_annotations: bool, cache: LookupCache, overwrite_existing_tier: bool):
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
    ignore_case=DEFAULT_IGNORE_CASE,
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
      new_arpa_tuple = words_arpa_with_punctuation.pop(0)
      # if new_arpa_tuple == ("sil",):
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


def transcribe_words_to_arpa_on_phoneme_level(grid: TextGrid, words_tier_name: str, phoneme_tier_name: str, arpa_tier_name: str, consider_annotations: bool, cache: LookupCache, overwrite_existing_tier: bool, trim_symbols: Set[Symbol]):
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
    ignore_case=DEFAULT_IGNORE_CASE,
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
