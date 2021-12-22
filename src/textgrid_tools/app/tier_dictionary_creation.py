from argparse import ArgumentParser
from logging import getLogger
from pathlib import Path
from typing import Callable, Iterable, List, cast

from pronunciation_dict_parser.default_parser import PublicDictType
from pronunciation_dict_parser.export import export
from textgrid.textgrid import TextGrid
from textgrid_tools.app.globals import DEFAULT_PUNCTUATION
from textgrid_tools.app.helper import (add_n_digits_argument,
                                       add_n_jobs_argument,
                                       add_overwrite_argument, get_grid_files,
                                       load_grid)
from textgrid_tools.core.mfa.tiers_dictionary_creation import (
    can_get_arpa_pronunciation_dicts_from_texts,
    get_arpa_pronunciation_dicts_from_texts)
from tqdm import tqdm


def init_convert_texts_to_dicts_parser(parser: ArgumentParser) -> Callable:
  arpa_dicts = [
    PublicDictType.MFA_ARPA,
    PublicDictType.CMU_ARPA,
    PublicDictType.LIBRISPEECH_ARPA,
    PublicDictType.PROSODYLAB_ARPA,
  ]
  parser.description = "With this command you can create an ARPA pronunciation dictionary out of all words from a tier in the grid files. This dictionary can then be used for alignment with the Montreal Forced Aligner (MFA). The words are determined by splitting the text on the tiers with the space symbol."
  parser.add_argument("input_directory", type=Path, metavar="input-directory",
                      help="the directory containing the grid files")
  parser.add_argument("tier", type=str, help="the tier that contains the words")
  parser.add_argument("output_file", type=Path, metavar="output-file",
                      help="the file containing the generated pronunciation dictionary")
  parser.add_argument("--punctuation", type=str, metavar='SYMBOL', nargs='*', default=DEFAULT_PUNCTUATION,
                      help="Trim these punctuation symbols from the start and end of a word before looking it up in the reference pronunciation dictionary.")
  add_n_digits_argument(parser)
  parser.add_argument("--consider-annotations", action="store_true",
                      help="consider /.../-style annotations")
  parser.add_argument("--include-punctuation-in-pronunciations", action="store_true",
                      help="include punctuation in the ARPA pronunciation")
  parser.add_argument("--include-punctuation-in-words", action="store_true",
                      help="include punctuation in the words")
  parser.add_argument("--split-on-hyphen", action="store_true",
                      help="split words on hyphen symbol before lookup")
  parser.add_argument("--dictionary", metavar='PATH', choices=arpa_dicts,
                      type=PublicDictType.__getitem__, default=PublicDictType.MFA_ARPA, help="the pronunciation dictionary on which the words should be looked up (if a word does not occur than its pronunciation will be estimated)")
  add_n_jobs_argument(parser)
  add_overwrite_argument(parser)
  return convert_texts_to_arpa_dicts


def convert_texts_to_arpa_dicts(input_directory: Path, tier: str, punctuation: List[str], consider_annotations: bool, include_punctuation_in_pronunciations: bool, include_punctuation_in_words: bool, split_on_hyphen: bool, n_jobs: int, output_file: Path, dictionary: PublicDictType, n_digits: int, overwrite: bool) -> None:
  logger = getLogger(__name__)

  if not input_directory.exists():
    logger.error("Textgrid folder does not exist!")
    return

  if output_file.is_file() and not overwrite:
    logger.error(f"{output_file} already exists!")
    return

  trim_symbols_set = set(punctuation)
  logger.info(
    f"Punctuation symbols: {' '.join(sorted(trim_symbols_set))} (#{len(trim_symbols_set)})")

  grid_files = get_grid_files(input_directory)
  logger.info(f"Found {len(grid_files)} grid files.")

  logger.info("Reading files...")
  grids: List[TextGrid] = []
  for file_stem in cast(Iterable[str], tqdm(grid_files)):
    logger.info(f"Processing {file_stem} ...")

    grid_file_in_abs = input_directory / grid_files[file_stem]
    grid_in = load_grid(grid_file_in_abs, n_digits)
    grids.append(grid_in)

  can_create_pronunciations = can_get_arpa_pronunciation_dicts_from_texts(grids, tier,
                                                                          include_punctuation_in_pronunciations,
                                                                          include_punctuation_in_words)
  if not can_create_pronunciations:
    return

  logger.info("Producing dictionary...")
  pronunciation_dict = get_arpa_pronunciation_dicts_from_texts(
    grids=grids,
    tier=tier,
    punctuation=trim_symbols_set,
    dict_type=dictionary,
    consider_annotations=consider_annotations,
    ignore_case=True,
    n_jobs=n_jobs,
    split_on_hyphen=split_on_hyphen,
    include_punctuation_in_pronunciations=include_punctuation_in_pronunciations,
    include_punctuation_in_words=include_punctuation_in_words,
  )

  logger.info(f"Saving {output_file} ...")
  export(
    include_counter=True,
    path=output_file,
    pronunciation_dict=pronunciation_dict,
    symbol_sep=" ",
    word_pronunciation_sep="  ",
  )
  logger.info(f"Written pronunciation dictionary to: \"{output_file}\".")

  return
