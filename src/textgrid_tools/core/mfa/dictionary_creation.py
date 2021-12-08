from collections import OrderedDict
from logging import getLogger
from typing import List, Set, Tuple

from ordered_set import OrderedSet
from pronunciation_dict_parser import PronunciationDict
from pronunciation_dict_parser.default_parser import PublicDictType
from sentence2pronunciation import LookupCache
from sentence2pronunciation.multiprocessing import prepare_cache_mp
from text_utils import Language, text_to_symbols
from text_utils.pronunciation.main import get_eng_to_arpa_lookup_method
from text_utils.symbol_format import SymbolFormat
from text_utils.text import text_to_sentences
from text_utils.types import Symbol
from text_utils.utils import symbols_ignore
from textgrid_tools.core.mfa.arpa import ALLOWED_MFA_MODEL_SYMBOLS, SIL
from tqdm import tqdm


def get_arpa_pronunciation_dicts_from_texts(texts: List[str], trim_symbols: Set[Symbol], dict_type: PublicDictType, ignore_case: bool, n_jobs: int, split_on_hyphen: bool, consider_annotations: bool) -> Tuple[PronunciationDict, PronunciationDict, LookupCache]:
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
    trim_symbols=trim_symbols,
    maxtasksperchild=None,
  )
  logger.info("Done.")

  logger.info("Creating pronunciation dictionary...")
  pronunciation_dict_no_punctuation: PronunciationDict = OrderedDict()
  pronunciation_dict_punctuation: PronunciationDict = OrderedDict()

  allowed_symbols = ALLOWED_MFA_MODEL_SYMBOLS
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
        f"The arpa of the word {''.join(unique_word)} contains only punctuation, therefore annotating \"{SIL}\".")
      arpa_symbols_no_punctuation = (SIL,)
    assert word_str not in pronunciation_dict_no_punctuation
    pronunciation_dict_no_punctuation[word_str] = OrderedSet([arpa_symbols_no_punctuation])
  logger.info("Done.")
  return pronunciation_dict_no_punctuation, pronunciation_dict_punctuation, cache
