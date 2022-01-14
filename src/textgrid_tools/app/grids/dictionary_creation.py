from argparse import ArgumentParser
from logging import getLogger
from pathlib import Path
from typing import Callable, List

from pronunciation_dict_parser import (PublicDictType, get_dict_from_name,
                                       save_dictionary_as_txt)
from text_utils.string_format import StringFormat
from textgrid.textgrid import TextGrid
from textgrid_tools.app.globals import DEFAULT_PUNCTUATION, ExecutionResult
from textgrid_tools.app.helper import (add_encoding_argument,
                                       add_grid_directory_argument,
                                       add_interval_format_argument,
                                       add_n_digits_argument,
                                       add_n_jobs_argument,
                                       add_overwrite_argument,
                                       add_string_format_argument,
                                       get_grid_files, load_grid)
from textgrid_tools.app.validation import (DirectoryNotExistsError,
                                           FileAlreadyExistsError)
from textgrid_tools.core import get_arpa_pronunciation_dictionary
from textgrid_tools.core.interval_format import IntervalFormat


def get_dictionary_creation_parser(parser: ArgumentParser) -> Callable:
  arpa_dicts = [
    PublicDictType.MFA_ARPA,
    PublicDictType.CMU_ARPA,
    PublicDictType.LIBRISPEECH_ARPA,
    PublicDictType.PROSODYLAB_ARPA,
  ]
  parser.description = "This command creates an ARPA pronunciation dictionary out of all words from a tier in the grid files. This dictionary can then be used for alignment with the Montreal Forced Aligner (MFA). The words are determined by splitting the text on the tiers with the space symbol."
  add_grid_directory_argument(parser)
  parser.add_argument("tiers", type=str, nargs="+", help="tiers that contains the English text")
  parser.add_argument("output", type=Path, metavar="output",
                      help="path to write the generated pronunciation dictionary")
  parser.add_argument("--dictionary", choices=arpa_dicts,
                      type=get_dict_from_name, default=PublicDictType.MFA_ARPA, help="the pronunciation dictionary on which the words should be looked up (if a word does not occur then its pronunciation will be estimated)")
  parser.add_argument("--punctuation", type=str, metavar='SYMBOL', nargs='*', default=DEFAULT_PUNCTUATION,
                      help="trim these punctuation symbols from the start and end of a word before looking it up in the reference pronunciation dictionary")
  add_n_digits_argument(parser)
  parser.add_argument("--consider-annotations", action="store_true",
                      help="consider /.../-styled annotations")
  parser.add_argument("--include-punctuation-in-pronunciations", action="store_true",
                      help="include punctuation in the ARPA pronunciation")
  parser.add_argument("--include-punctuation-in-words", action="store_true",
                      help="include punctuation in the words")
  parser.add_argument("--split-on-hyphen", action="store_true",
                      help="split words on hyphen symbol before lookup")
  add_n_jobs_argument(parser)
  parser.add_argument("--chunksize", type=int, metavar="NUMBER",
                      help="amount of words to chunk into one job", default=500)
  add_encoding_argument(parser, "output encoding")
  add_string_format_argument(parser, "--tiers-format", "format of tiers")
  add_interval_format_argument(parser, "--tiers-type", "type of tiers")
  add_overwrite_argument(parser)
  return app_get_arpa_pronunciation_dictionary


def app_get_arpa_pronunciation_dictionary(directory: Path, dictionary: PublicDictType, tiers: List[str], punctuation: List[str], consider_annotations: bool, include_punctuation_in_pronunciations: bool, include_punctuation_in_words: bool, split_on_hyphen: bool, n_jobs: int, chunksize: int, tiers_type: IntervalFormat, tiers_format: StringFormat, output: Path, encoding: str, n_digits: int, overwrite: bool) -> ExecutionResult:
  logger = getLogger(__name__)

  if error := DirectoryNotExistsError.validate(directory):
    logger.error(error.default_message)
    return False, False

  if not overwrite and (error := FileAlreadyExistsError(output)):
    logger.error(error.default_message)
    return False, False

  grid_files = get_grid_files(directory)

  grids: List[TextGrid] = []
  for file_nr, (file_stem, rel_path) in enumerate(grid_files.items(), start=1):
    logger.info(f"Reading {file_stem} ({file_nr}/{len(grid_files)})...")
    grid_file_in_abs = directory / rel_path
    grid_in = load_grid(grid_file_in_abs, n_digits)
    grids.append(grid_in)

  logger.info("Producing dictionary...")
  (error, changed_anything), pronunciation_dict = get_arpa_pronunciation_dictionary(
    grids=grids,
    dictionary=dictionary,
    punctuation=set(punctuation),
    consider_annotations=consider_annotations,
    n_jobs=n_jobs,
    split_on_hyphen=split_on_hyphen,
    include_punctuation_in_pronunciations=include_punctuation_in_pronunciations,
    include_punctuation_in_words=include_punctuation_in_words,
    chunksize=chunksize,
    tier_names=set(tiers),
    tiers_interval_format=tiers_type,
    tiers_string_format=tiers_format,
  )

  assert not changed_anything
  success = error is None

  if not success:
    logger.error(error.default_message)
    return False, False

  logger.info("Saving dictionary...")
  save_dictionary_as_txt(
    include_counter=True,
    path=output,
    pronunciation_dict=pronunciation_dict,
    symbol_sep=" ",
    word_pronunciation_sep="  ",
    empty_symbol="",
    encoding=encoding,
    only_first_pronunciation=False,
  )

  return True, True
