from collections import OrderedDict
from logging import getLogger
from typing import Iterable, List, Set, Tuple, cast

from ordered_set import OrderedSet
from pronunciation_dict_parser import PronunciationDict
from pronunciation_dict_parser.default_parser import PublicDictType
from pronunciation_dict_parser.parser import Pronunciation
from sentence2pronunciation.multiprocessing import prepare_cache_mp
from text_utils import Language, text_to_symbols
from text_utils.pronunciation.main import get_eng_to_arpa_lookup_method
from text_utils.symbol_format import SymbolFormat
from text_utils.text import text_to_sentences
from text_utils.types import Symbol
from text_utils.utils import symbols_ignore
from textgrid import TextGrid
from textgrid_tools.core.mfa.arpa import ALLOWED_MFA_MODEL_SYMBOLS, SIL
from textgrid_tools.core.mfa.helper import (check_is_valid_grid,
                                            get_first_tier, tier_exists,
                                            tier_to_text)
from tqdm import tqdm


def can_get_arpa_pronunciation_dicts_from_texts(grids: List[TextGrid], tier: str, include_punctuation_in_pronunciations: bool, include_punctuation_in_words: bool) -> bool:
  logger = getLogger(__name__)
  if len(grids) == 0:
    logger.error("No grids found!")
    return False

  for grid in grids:
    if not check_is_valid_grid(grid):
      logger.error("Grid is invalid!")
      return False

    if not tier_exists(grid, tier):
      logger.info("Tier does not exist.")
      return False

  if not include_punctuation_in_words:
    if include_punctuation_in_pronunciations:
      logger.info(
        "If punctuation should not be included in the words, it needs to be ignored in the pronunciations, too.")
      return False
  return True


def get_arpa_pronunciation_dicts_from_texts(grids: List[TextGrid], tier: str, punctuation: Set[Symbol], dict_type: PublicDictType, ignore_case: bool, n_jobs: int, split_on_hyphen: bool, consider_annotations: bool, include_punctuation_in_pronunciations: bool, include_punctuation_in_words: bool) -> PronunciationDict:
  assert can_get_arpa_pronunciation_dicts_from_texts(
    grids, tier, include_punctuation_in_pronunciations, include_punctuation_in_words)
  logger = getLogger(__name__)
  logger.info(f"Chosen dictionary type: {dict_type}")
  assert include_punctuation_in_words or not include_punctuation_in_pronunciations

  logger.info("Getting all sentences...")
  texts = []
  for grid in grids:
    target_tier = get_first_tier(grid, tier)
    text = tier_to_text(target_tier, join_with=" ")
    texts.append(text)

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

  logger.info("Converting all words to ARPA...")
  cache = prepare_cache_mp(
    sentences=text_sentences,
    annotation_split_symbol="/",
    chunksize=500,
    consider_annotation=consider_annotations,
    get_pronunciation=get_eng_to_arpa_lookup_method(),
    ignore_case=ignore_case,
    n_jobs=n_jobs,
    split_on_hyphen=split_on_hyphen,
    trim_symbols=punctuation,
    maxtasksperchild=None,
  )
  logger.info("Done.")

  logger.info("Creating pronunciation dictionary...")
  result: PronunciationDict = OrderedDict()

  allowed_symbols = ALLOWED_MFA_MODEL_SYMBOLS
  for unique_word, arpa_symbols in cast(Iterable[Tuple[Pronunciation, Pronunciation]], tqdm(sorted(cache.items()))):
    assert len(unique_word) > 0
    assert len(arpa_symbols) > 0

    if include_punctuation_in_words:
      word_str = "".join(unique_word)
    else:
      unique_word_no_punctuation = symbols_ignore(unique_word, punctuation)
      word_str = "".join(unique_word_no_punctuation)
      if word_str in result:
        continue

    # maybe ignore spn here
    if include_punctuation_in_pronunciations:
      final_word_symbols = arpa_symbols
    else:
      arpa_symbols_no_punctuation = symbols_ignore(arpa_symbols, punctuation)
      not_allowed_symbols = {
        symbol for symbol in arpa_symbols_no_punctuation if symbol not in allowed_symbols}
      if len(not_allowed_symbols) > 0:
        logger.warning(
          "Not all symbols can be aligned! You have missed some trim-symbols or annotated non-existent ARPA symbols!")
        logger.info(
          f"Word containing not allowed symbols: {' '.join(sorted(not_allowed_symbols))} ({''.join(unique_word)} -> {''.join(arpa_symbols)})")

      arpa_contains_only_punctuation = len(arpa_symbols_no_punctuation) == 0
      if arpa_contains_only_punctuation:
        arpa_symbols_no_punctuation = (SIL,)
        logger.info(
          f"The ARPA of the word {''.join(unique_word)} contained only punctuation, therefore \"{SIL}\" was annotated.")
      final_word_symbols = arpa_symbols_no_punctuation
      
    assert word_str not in result
    result[word_str] = OrderedSet([final_word_symbols])
    
  logger.info("Done.")

  return result
