from argparse import ArgumentParser
from logging import getLogger
from pathlib import Path
from typing import Iterable, List, cast

from general_utils.main import load_obj
from textgrid_tools.app.globals import DEFAULT_N_DIGITS
from textgrid_tools.app.helper import get_grid_files, load_grid, save_grid
from textgrid_tools.core.mfa.tier_words_to_arpa_transcription import (
    can_transcribe_words_to_arpa_on_phoneme_level,
    transcribe_words_to_arpa_on_phoneme_level)
from tqdm import tqdm


def init_app_transcribe_words_to_arpa_on_phoneme_level_parser(parser: ArgumentParser):
  parser.add_argument("--grid_folder_in", type=Path, required=True)
  parser.add_argument("--words_tier", type=str, required=True)
  parser.add_argument("--phoneme_tier", type=str, required=True)
  parser.add_argument("--new_tier", type=str, required=True)
  parser.add_argument("--consider_annotations", action="store_true")
  parser.add_argument("--path_cache", type=Path, required=True)
  parser.add_argument("--trim_symbols", type=str, nargs="*", required=True)
  parser.add_argument("--n_digits", type=int, default=DEFAULT_N_DIGITS)
  parser.add_argument("--overwrite_tier", action="store_true")
  parser.add_argument("--grid_folder_out", type=Path, required=True)
  parser.add_argument("--overwrite", action="store_true")
  return app_transcribe_words_to_arpa_on_phoneme_level


def app_transcribe_words_to_arpa_on_phoneme_level(grid_folder_in: Path, words_tier: str, phoneme_tier: str, new_tier: str, consider_annotations: bool, path_cache: Path, trim_symbols: List[str], n_digits: int, overwrite_tier: bool, grid_folder_out: Path, overwrite: bool) -> None:
  logger = getLogger(__name__)

  if not grid_folder_in.exists():
    logger.error("Textgrid folder does not exist!")
    return

  grid_files = get_grid_files(grid_folder_in)
  logger.info(f"Found {len(grid_files)} grid files.")

  cache = load_obj(path_cache)

  trim_symbols_set = set(trim_symbols)
  logger.info(f"Trim symbols: {' '.join(sorted(trim_symbols_set))} (#{len(trim_symbols_set)})")

  logger.info("Reading files...")
  for file_stem in cast(Iterable[str], tqdm(grid_files)):
    logger.info(f"Processing {file_stem} ...")

    grid_file_out_abs = grid_folder_out / grid_files[file_stem]

    if grid_file_out_abs.exists() and not overwrite:
      logger.info("Target grid already exists.")
      logger.info("Skipped.")
      continue

    grid_file_in_abs = grid_folder_in / grid_files[file_stem]
    grid_in = load_grid(grid_file_in_abs, n_digits)

    can_map = can_transcribe_words_to_arpa_on_phoneme_level(
      grid=grid_in,
      new_tier=new_tier,
      overwrite_tier=overwrite_tier,
      phoneme_tier=phoneme_tier,
      words_tier=words_tier,
    )

    if not can_map:
      logger.info("Skipped.")
      continue

    transcribe_words_to_arpa_on_phoneme_level(
      grid=grid_in,
      new_tier=new_tier,
      overwrite_tier=overwrite_tier,
      phoneme_tier=phoneme_tier,
      words_tier=words_tier,
      cache=cache,
      consider_annotations=consider_annotations,
      ignore_case=True,
      trim_symbols=trim_symbols_set,
    )

    logger.info("Saving...")
    save_grid(grid_file_out_abs, grid_in)

  logger.info(f"Done. Written output to: {grid_folder_out}")
