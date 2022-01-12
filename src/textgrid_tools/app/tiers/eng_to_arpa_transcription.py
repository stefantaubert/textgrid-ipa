from argparse import ArgumentParser
from functools import partial
from logging import getLogger
from pathlib import Path
from typing import Iterable, List, Optional, Set, cast

from pronunciation_dict_parser.parser import parse_file
from text_utils.string_format import StringFormat
from textgrid_tools.app.globals import DEFAULT_PUNCTUATION, ExecutionResult
from textgrid_tools.app.helper import (add_n_digits_argument,
                                       add_overwrite_argument,
                                       add_overwrite_tier_argument,
                                       get_grid_files, load_grid, save_grid)
from textgrid_tools.app.tier.common import process_grids
from textgrid_tools.app.validation import FileNotExistsError
from textgrid_tools.core import transcribe_eng_text_to_arpa
from tqdm import tqdm


def init_app_transcribe_words_to_arpa_on_phoneme_level_parser(parser: ArgumentParser):
  parser.description = "This command transcribes words to ARPA on phoneme level."
  parser.add_argument("input_directory", type=Path, metavar="input-directory",
                      help="the directory containing the grid files")
  parser.add_argument("words_tier", metavar="words-tier", type=str,
                      help="the tier containing the words")
  parser.add_argument("phoneme_tier", metavar="phoneme-tier", type=str,
                      help="the tier containing the phonemes")
  parser.add_argument("new_tier", metavar="new-tier", type=str,
                      help="the name of the tier to which the transcription should be written")
  parser.add_argument("dictionary_file", metavar="dictionary-file", type=Path,
                      help="the path to the pronunciation dictionary")
  parser.add_argument("--trim-symbols", metavar="SYMBOL", type=str,
                      nargs="*", default=DEFAULT_PUNCTUATION, help="symbols which should be merged to the corresponding ARPA characters.")
  add_n_digits_argument(parser)
  parser.add_argument("--output-directory", metavar="PATH", type=Path,
                      help="the directory where to output the modified grid files if not to input-directory")
  add_overwrite_tier_argument(parser)
  add_overwrite_argument(parser)
  return app_transcribe_words_to_arpa_on_phoneme_level


def app_transcribe_words_to_arpa_on_phoneme_level(directory: Path, tiers: Set[str], tiers_format: StringFormat, dictionary: Path, encoding: str, chunksize: int, n_jobs: int, n_digits: int, output_directory: Optional[Path], overwrite: bool) -> ExecutionResult:
  if error := FileNotExistsError.validate(dictionary):
    logger = getLogger(__name__)
    logger.error(error.default_message)
    return False, False

  pronunciation_dictionary = parse_file(dictionary, encoding)

  method = partial(
    transcribe_eng_text_to_arpa,
    chunksize=chunksize,
    n_jobs=n_jobs,
    pronunciation_dictionary=pronunciation_dictionary,
    tier_names=set(tiers),
    tiers_string_format=tiers_format,
  )

  return process_grids(directory, n_digits, output_directory, overwrite, method)
