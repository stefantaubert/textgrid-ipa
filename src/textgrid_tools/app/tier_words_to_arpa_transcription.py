from argparse import ArgumentParser
from logging import getLogger
from pathlib import Path
from typing import Iterable, List, Optional, cast

from pronunciation_dict_parser.parser import parse_file
from textgrid_tools.app.globals import DEFAULT_PUNCTUATION
from textgrid_tools.app.helper import (add_n_digits_argument,
                                       add_overwrite_argument,
                                       add_overwrite_tier_argument,
                                       get_grid_files, load_grid, save_grid)
from textgrid_tools.core.mfa.tier_words_to_arpa_transcription import (
    can_transcribe_words_to_arpa_on_phoneme_level,
    transcribe_words_to_arpa_on_phoneme_level)
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


def app_transcribe_words_to_arpa_on_phoneme_level(input_directory: Path, words_tier: str, phoneme_tier: str, new_tier: str, dictionary_file: Path, trim_symbols: List[str], n_digits: int, overwrite_tier: bool, output_directory: Optional[Path], overwrite: bool) -> None:
  logger = getLogger(__name__)

  if not input_directory.exists():
    logger.error("Input directory does not exist!")
    return

  if not dictionary_file.exists():
    logger.error("Pronunciation dictionary was not found!")
    return

  if output_directory is None:
    output_directory = input_directory

  grid_files = get_grid_files(input_directory)
  logger.info(f"Found {len(grid_files)} grid files.")

  pronunciation_dictionary = parse_file(dictionary_file, encoding="UTF-8")

  trim_symbols_set = set(trim_symbols)
  logger.info(f"Trim symbols: {' '.join(sorted(trim_symbols_set))} (#{len(trim_symbols_set)})")

  logger.info("Reading files...")
  for file_stem in cast(Iterable[str], tqdm(grid_files)):
    logger.info(f"Processing {file_stem} ...")

    grid_file_out_abs = output_directory / grid_files[file_stem]

    if grid_file_out_abs.exists() and not overwrite:
      logger.info("Grid already exists.")
      logger.info("Skipped.")
      continue

    grid_file_in_abs = input_directory / grid_files[file_stem]
    grid_in = load_grid(grid_file_in_abs, n_digits)

    can_transcribe = can_transcribe_words_to_arpa_on_phoneme_level(
      grid=grid_in,
      new_tier=new_tier,
      overwrite_tier=overwrite_tier,
      phoneme_tier=phoneme_tier,
      words_tier=words_tier,
    )

    if not can_transcribe:
      logger.info("Skipped.")
      continue

    transcribe_words_to_arpa_on_phoneme_level(
      grid=grid_in,
      new_tier=new_tier,
      overwrite_tier=overwrite_tier,
      phoneme_tier=phoneme_tier,
      words_tier=words_tier,
      ignore_case=True,
      pronunciation_dictionary=pronunciation_dictionary,
      trim_symbols=trim_symbols_set,
    )

    logger.info("Saving...")
    save_grid(grid_file_out_abs, grid_in)

  logger.info(f"Done. Written output to: {output_directory}")

# def init_app_transcribe_words_to_arpa_parser(parser: ArgumentParser):
#   parser.add_argument("--folder_in", type=Path, required=True)
#   parser.add_argument("--original_text_tier_name", type=str, required=True)
#   parser.add_argument("--tier_name", type=str, required=True)
#   parser.add_argument("--overwrite_existing_tier", action="store_true")
#   parser.add_argument("--path_cache", type=Path, required=True)
#   parser.add_argument("--folder_out", type=Path, required=True)
#   parser.add_argument("--consider_annotations", action="store_true")
#   parser.add_argument("--overwrite", action="store_true")
#   return app_transcribe_words_to_arpa


# def app_transcribe_words_to_arpa(base_dir: Path, folder_in: Path, original_text_tier_name: str, consider_annotations: bool, tier_name: str, overwrite_existing_tier: bool, path_cache: Path, folder_out: Path, overwrite: bool):
#   logger = getLogger(__name__)

#   if not folder_in.exists():
#     raise Exception("Folder does not exist!")

#   if not path_cache.exists():
#     raise Exception("Cache not found!")

#   cache = cast(LookupCache, load_obj(path_cache))

#   all_files = get_filepaths(folder_in)
#   textgrid_files = [file for file in all_files if str(file).endswith(".TextGrid")]
#   logger.info(f"Found {len(textgrid_files)} .TextGrid files.")

#   textgrid_file_in: Path
#   for textgrid_file_in in tqdm(textgrid_files):
#     textgrid_file_out = folder_out / textgrid_file_in.name
#     if textgrid_file_out.exists() and not overwrite:
#       logger.info(f"Skipped already existing file: {textgrid_file_in.name}")
#       continue

#     logger.debug(f"Processing {textgrid_file_in}...")

#     grid = TextGrid()
#     grid.read(textgrid_file_in, round_digits=DEFAULT_TEXTGRID_PRECISION)

#     transcribe_words_to_arpa(
#       grid=grid,
#       tier_name=tier_name,
#       original_text_tier_name=original_text_tier_name,
#       cache=cache,
#       overwrite_existing_tier=overwrite_existing_tier,
#       consider_annotations=consider_annotations,
#       ignore_case=True,
#     )

#     folder_out.mkdir(parents=True, exist_ok=True)
#     grid.write(textgrid_file_out)

#   logger.info(f"Written output .TextGrid files to: {folder_out}")
