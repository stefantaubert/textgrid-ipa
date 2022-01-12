from logging import getLogger
from typing import Iterable, List, Optional, Set, Tuple, cast

from ordered_set import OrderedSet
from pronunciation_dict_parser import PronunciationDict
from pronunciation_dict_parser.parser import Pronunciation
from sentence2pronunciation.lookup_cache import LookupCache
from sentence2pronunciation.multiprocessing import prepare_cache_mp
from text_utils.pronunciation.main import get_eng_to_arpa_lookup_method
from text_utils.string_format import StringFormat
from text_utils.types import Symbol, Symbols
from text_utils.utils import symbols_ignore, symbols_split
from textgrid import TextGrid
from textgrid.textgrid import Interval, IntervalTier
from textgrid_tools.core.globals import ExecutionResult
from textgrid_tools.core.grids.arpa import ALLOWED_MFA_MODEL_SYMBOLS, SIL
from textgrid_tools.core.helper import (get_all_tiers,
                                        get_mark_symbols_intervals)
from textgrid_tools.core.interval_format import IntervalFormat
from textgrid_tools.core.validation import (InvalidGridError,
                                            InvalidStringFormatIntervalError,
                                            NotExistingTierError,
                                            NotMatchingIntervalFormatError,
                                            ValidationError)
from tqdm import tqdm


class PunctuationFormatNotSupportedError(ValidationError):
  @classmethod
  def validate(cls, include_punctuation_in_words: bool, include_punctuation_in_pronunciations: bool):
    if not include_punctuation_in_words and include_punctuation_in_pronunciations:
      return cls()
    return None

  @property
  def default_message(self) -> str:
    return "If punctuation should not be included in the words, it needs to be ignored in the pronunciations, too."


def get_arpa_pronunciation_dictionary(grids: List[TextGrid], tier_names: Set[str], tiers_string_format: StringFormat, tiers_interval_format: IntervalFormat, punctuation: Set[Symbol], split_on_hyphen: bool, consider_annotations: bool, include_punctuation_in_pronunciations: bool, include_punctuation_in_words: bool, n_jobs: int, chunksize: int) -> Tuple[ExecutionResult, Optional[PronunciationDict]]:
  assert len(grids) > 0
  assert len(tier_names) > 0
  assert tiers_interval_format in (IntervalFormat.WORD, IntervalFormat.WORDS)

  if error := PunctuationFormatNotSupportedError.validate(include_punctuation_in_words, include_punctuation_in_pronunciations):
    return (error, False), None

  all_tiers: List[IntervalTier] = []
  for grid in grids:
    if error := InvalidGridError.validate(grid):
      return (error, False), None

    for tier_name in tier_names:
      if error := NotExistingTierError.validate(grid, tier_name):
        return (error, False), None

    tiers = list(get_all_tiers(grid, tier_names))

    for tier in tiers:
      if error := InvalidStringFormatIntervalError.validate_tier(tier, tiers_string_format):
        return (error, False), None

      if error := NotMatchingIntervalFormatError.validate_tier(tier, tiers_interval_format, tiers_string_format):
        return (error, False), None
    all_tiers.extend(tiers)

  logger = getLogger(__name__)
  # logger.debug(f"Chosen dictionary type: {dict_type}")

  # logger.info(f"Punctuation symbols: {' '.join(sorted(punctuation))} (#{len(punctuation)})")

  words = get_word_symbols_from_tiers(all_tiers, tiers_string_format)
  logger.debug(f"Retrieved {len(words)} unique words.")

  logger.debug("Converting all words to ARPA...")
  cache = prepare_cache_mp(
    sentences=words,
    annotation_split_symbol="/",
    chunksize=chunksize,
    consider_annotation=consider_annotations,
    get_pronunciation=get_eng_to_arpa_lookup_method(),
    ignore_case=True,
    n_jobs=n_jobs,
    split_on_hyphen=split_on_hyphen,
    trim_symbols=punctuation,
    maxtasksperchild=None,
  )
  logger.debug("Done.")

  logger.debug("Creating pronunciation dictionary...")
  result = get_pronunciation_dictionary(
    cache, include_punctuation_in_pronunciations, include_punctuation_in_words, punctuation)

  check_pronunciation_dictionary_for_silence(result)
  check_pronunciation_dictionary_for_invalid_mfa_symbols(result)

  return (None, True), result


def check_pronunciation_dictionary_for_silence(result: PronunciationDict) -> None:
  logger = getLogger(__name__)
  for word, pronunciations in result.items():
    pronunciation = pronunciations[0]
    if pronunciation == (SIL,):
      logger.info(
        f"The ARPA of the word {word} contained only punctuation, therefore \"{SIL}\" was annotated.")


def check_pronunciation_dictionary_for_invalid_mfa_symbols(result: PronunciationDict) -> None:
  logger = getLogger(__name__)
  for word, pronunciations in result.items():
    pronunciation = pronunciations[0]
    not_allowed_symbols = {
      symbol
      for symbol in pronunciation
      if symbol not in ALLOWED_MFA_MODEL_SYMBOLS
    }

    if len(not_allowed_symbols) > 0:
      logger.warning(
        "Not all symbols can be aligned! You have missed some trim-symbols or annotated non-existent ARPA symbols!")
      logger.info(
        f"Word containing not allowed symbols: {' '.join(sorted(not_allowed_symbols))} ({word} -> {''.join(pronunciation)})")


def get_pronunciation_dictionary(cache: LookupCache, include_punctuation_in_pronunciations: bool, include_punctuation_in_words: bool, punctuation: Set[Symbol]):
  result = PronunciationDict()

  for word_symbols, word_arpa_symbols in cast(Iterable[Tuple[Pronunciation, Pronunciation]], tqdm(sorted(cache.items()))):
    if len(word_symbols) == 0:
      continue
    assert len(word_arpa_symbols) > 0

    if include_punctuation_in_words:
      word_str = "".join(word_symbols)
      assert word_str not in result
    else:
      unique_word_no_punctuation = symbols_ignore(word_symbols, punctuation)
      word_str = "".join(unique_word_no_punctuation)
      if word_str in result:
        continue

    # maybe ignore spn here
    if include_punctuation_in_pronunciations:
      final_word_symbols = word_arpa_symbols
    else:
      final_word_symbols = symbols_ignore(word_arpa_symbols, punctuation)

      arpa_contains_only_punctuation = len(final_word_symbols) == 0
      if arpa_contains_only_punctuation:
        final_word_symbols = (SIL,)

    result[word_str] = OrderedSet([final_word_symbols])
  return result


def get_word_symbols_from_tiers(tiers: Iterable[IntervalTier], tiers_string_format: StringFormat) -> Set[Symbols]:
  all_intervals = (
    interval
    for tier in tiers
    for interval in cast(
        Iterable[Interval], tier.intervals)
  )

  words = {
    word
    for interval_symbols in get_mark_symbols_intervals(all_intervals, tiers_string_format)
    for word in symbols_split(interval_symbols, " ")
  }

  return words


# def get_arpa_pronunciation_dicts_from_texts(grids: List[TextGrid], tier: str, punctuation: Set[Symbol], dict_type: PublicDictType, ignore_case: bool, n_jobs: int, split_on_hyphen: bool, consider_annotations: bool, include_punctuation_in_pronunciations: bool, include_punctuation_in_words: bool) -> PronunciationDict:
#   assert can_get_arpa_pronunciation_dicts_from_texts(
#     grids, tier, include_punctuation_in_pronunciations, include_punctuation_in_words)
#   logger = getLogger(__name__)
#   logger.info(f"Chosen dictionary type: {dict_type}")
#   assert include_punctuation_in_words or not include_punctuation_in_pronunciations

#   logger.info("Getting all sentences...")
#   texts = []
#   for grid in grids:
#     target_tier = get_first_tier(grid, tier)
#     # TODO
#     text = merge_intervals(target_tier, StringFormat.TEXT, IntervalFormat.WORDS)
#     texts.append(text)

#   text_sentences = {
#     text_to_symbols(
#       lang=Language.ENG,
#       text=sentence,
#       text_format=SymbolFormat.GRAPHEMES,
#     )
#     for text in tqdm(texts)
#     for sentence in text_to_sentences(
#       text=text,
#       text_format=SymbolFormat.GRAPHEMES,
#       lang=Language.ENG
#     )
#   }

#   logger.info(f"Done. Retrieved {len(text_sentences)} unique sentences.")

#   logger.info("Converting all words to ARPA...")
#   cache = prepare_cache_mp(
#     sentences=text_sentences,
#     annotation_split_symbol="/",
#     chunksize=500,
#     consider_annotation=consider_annotations,
#     get_pronunciation=get_eng_to_arpa_lookup_method(),
#     ignore_case=ignore_case,
#     n_jobs=n_jobs,
#     split_on_hyphen=split_on_hyphen,
#     trim_symbols=punctuation,
#     maxtasksperchild=None,
#   )
#   logger.info("Done.")

#   logger.info("Creating pronunciation dictionary...")
#   result: PronunciationDict = OrderedDict()

#   allowed_symbols = ALLOWED_MFA_MODEL_SYMBOLS
#   for unique_word, arpa_symbols in cast(Iterable[Tuple[Pronunciation, Pronunciation]], tqdm(sorted(cache.items()))):
#     assert len(unique_word) > 0
#     assert len(arpa_symbols) > 0

#     if include_punctuation_in_words:
#       word_str = "".join(unique_word)
#     else:
#       unique_word_no_punctuation = symbols_ignore(unique_word, punctuation)
#       word_str = "".join(unique_word_no_punctuation)
#       if word_str in result:
#         continue

#     # maybe ignore spn here
#     if include_punctuation_in_pronunciations:
#       final_word_symbols = arpa_symbols
#     else:
#       arpa_symbols_no_punctuation = symbols_ignore(arpa_symbols, punctuation)
#       not_allowed_symbols = {
#         symbol for symbol in arpa_symbols_no_punctuation if symbol not in allowed_symbols}
#       if len(not_allowed_symbols) > 0:
#         logger.warning(
#           "Not all symbols can be aligned! You have missed some trim-symbols or annotated non-existent ARPA symbols!")
#         logger.info(
#           f"Word containing not allowed symbols: {' '.join(sorted(not_allowed_symbols))} ({''.join(unique_word)} -> {''.join(arpa_symbols)})")

#       arpa_contains_only_punctuation = len(arpa_symbols_no_punctuation) == 0
#       if arpa_contains_only_punctuation:
#         arpa_symbols_no_punctuation = (SIL,)
#         logger.info(
#           f"The ARPA of the word {''.join(unique_word)} contained only punctuation, therefore \"{SIL}\" was annotated.")
#       final_word_symbols = arpa_symbols_no_punctuation

#     assert word_str not in result
#     result[word_str] = OrderedSet([final_word_symbols])

#   logger.info("Done.")

#   return result
