from argparse import ArgumentParser
from collections import OrderedDict
from logging import getLogger
from pathlib import Path
from typing import Callable, List

from ordered_set import OrderedSet
from pronunciation_dict_parser import PublicDictType, save_dictionary_as_txt
from text_utils.string_format import StringFormat
from textgrid.textgrid import TextGrid
from textgrid_tools.app.globals import DEFAULT_PUNCTUATION, ExecutionResult
from textgrid_tools.app.helper import (ConvertToOrderedSetAction,
                                       add_chunksize_argument,
                                       add_directory_argument,
                                       add_encoding_argument,
                                       add_interval_format_argument,
                                       add_n_digits_argument,
                                       add_n_jobs_argument,
                                       add_overwrite_argument,
                                       add_string_format_argument,
                                       add_tiers_argument, get_grid_files,
                                       load_grid, parse_non_empty, parse_path)
from textgrid_tools.app.validation import FileAlreadyExistsError
from textgrid_tools.core import get_arpa_pronunciation_dictionary
from textgrid_tools.core.interval_format import IntervalFormat


def add_dictionary_argument(parser: ArgumentParser) -> None:
  names = OrderedDict((
    (PublicDictType.MFA_ARPA, "MFA"),
    (PublicDictType.CMU_ARPA, "CMU"),
    (PublicDictType.LIBRISPEECH_ARPA, "LibriSpeech"),
    (PublicDictType.PROSODYLAB_ARPA, "Prosodylab"),
  ))

  values_to_names = dict(zip(
    names.values(),
    names.keys()
  ))

  help_str = "pronunciation dictionary (ARPAbet) which should be used to look up the words; if a pronunciation is not available it will be estimated"
  parser.add_argument(
    "-d", "--dictionary",
    metavar=list(names.values()),
    choices=PublicDictType,
    type=values_to_names.get,
    default=names[PublicDictType.MFA_ARPA],
    help=help_str,
  )


def get_dictionary_creation_parser(parser: ArgumentParser) -> Callable:
  parser.description = "This command creates an ARPAbet pronunciation dictionary out of all words from a tier in the grid files. This dictionary can then be used for alignment with Montreal Forced Aligner (MFA). The words are determined by splitting the text on the tiers with the space symbol."
  add_directory_argument(parser)
  parser.add_argument("output", type=parse_path, metavar="output",
                      help="path to write the generated pronunciation dictionary")
  add_tiers_argument(parser, "tiers that contains the English text")
  add_dictionary_argument(parser)
  parser.add_argument("--punctuation", type=parse_non_empty, metavar='SYMBOL', nargs='*', default=DEFAULT_PUNCTUATION,
                      help="trim these punctuation symbols from the start and end of a word before looking it up in the reference pronunciation dictionary", action=ConvertToOrderedSetAction)
  add_n_digits_argument(parser)
  parser.add_argument("--consider-annotations", action="store_true",
                      help="consider /.../-styled annotations")
  parser.add_argument("--include-punctuation-in-pronunciations", action="store_true",
                      help="include punctuation in the ARPA pronunciation")
  parser.add_argument("--include-punctuation-in-words", action="store_true",
                      help="include punctuation in the words")
  parser.add_argument("--split-on-hyphen", action="store_true",
                      help="split words on hyphen symbol before lookup")
  parser.add_argument("--is-already-transcription", action="store_true",
                      help="don't lookup words because they are already transcribed")
  add_n_jobs_argument(parser)
  add_chunksize_argument(parser, "words", 500)
  add_encoding_argument(parser, "output encoding")
  add_string_format_argument(parser, "tiers")
  add_interval_format_argument(parser, "tiers")
  add_overwrite_argument(parser)
  return app_get_arpa_pronunciation_dictionary


def app_get_arpa_pronunciation_dictionary(directory: Path, dictionary: PublicDictType, tiers: OrderedSet[str], punctuation: OrderedSet[str], consider_annotations: bool, include_punctuation_in_pronunciations: bool, include_punctuation_in_words: bool, split_on_hyphen: bool, n_jobs: int, chunksize: int, content: IntervalFormat, formatting: StringFormat, is_already_transcription: bool, output: Path, encoding: str, n_digits: int, overwrite: bool) -> ExecutionResult:
  logger = getLogger(__name__)

  if not overwrite and (error := FileAlreadyExistsError.validate(output)):
    logger.error(error.default_message)
    return False, False

  grid_files = get_grid_files(directory)

  logger.debug(f"Chosen dictionary type: {dictionary!r}")
  logger.debug(f"Punctuation symbols: {' '.join(sorted(punctuation))} (#{len(punctuation)})")

  grids: List[TextGrid] = []
  for file_nr, (file_stem, rel_path) in enumerate(grid_files.items(), start=1):
    logger.info(f"Reading {file_stem} ({file_nr}/{len(grid_files)})...")
    grid_file_in_abs = directory / rel_path
    grid_in = load_grid(grid_file_in_abs, n_digits)
    grids.append(grid_in)

  logger.info("Producing dictionary...")
  (error, _), pronunciation_dict = get_arpa_pronunciation_dictionary(
    grids=grids,
    dictionary=dictionary,
    punctuation=punctuation,
    consider_annotations=consider_annotations,
    n_jobs=n_jobs,
    split_on_hyphen=split_on_hyphen,
    include_punctuation_in_pronunciations=include_punctuation_in_pronunciations,
    include_punctuation_in_words=include_punctuation_in_words,
    chunksize=chunksize,
    tier_names=tiers,
    tiers_interval_format=content,
    tiers_string_format=formatting,
    is_already_transcription=is_already_transcription,
  )

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
