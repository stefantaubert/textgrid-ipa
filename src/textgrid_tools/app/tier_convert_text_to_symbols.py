from argparse import ArgumentParser
from logging import getLogger
from pathlib import Path
from typing import Iterable, cast

from textgrid_tools.app.globals import DEFAULT_N_DIGITS
from textgrid_tools.app.helper import get_grid_files, load_grid, save_grid
from textgrid_tools.core.mfa.tier_convert_text_to_symbols import (
    can_convert_text_to_symbols, convert_text_to_symbols)
from tqdm import tqdm


def init_files_convert_text_to_symbols_parser(parser: ArgumentParser):
  parser.description = "This command converts text in TEXT format to the SYMBOL format."
  parser.add_argument("--grid_folder_in", type=Path, required=True)
  parser.add_argument("--tier", type=str, required=True)
  parser.add_argument("--new_tier", type=str, required=True)
  parser.add_argument("--n_digits", type=int, default=DEFAULT_N_DIGITS)
  parser.add_argument("--grid_folder_out", type=Path, required=True)
  parser.add_argument("--overwrite", action="store_true")
  return files_convert_text_to_symbols


def files_convert_text_to_symbols(grid_folder_in: Path, tier: str, new_tier: str, n_digits: int, grid_folder_out: Path, overwrite: bool) -> None:
  logger = getLogger(__name__)

  if not grid_folder_in.exists():
    logger.error("Textgrid folder does not exist!")
    return

  grid_files = get_grid_files(grid_folder_in)
  logger.info(f"Found {len(grid_files)} grid files.")

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

    can_rename = can_convert_text_to_symbols(grid_in, tier)
    if not can_rename:
      logger.info("Skipped.")
      continue

    convert_text_to_symbols(grid_in, tier, new_tier)

    logger.info("Saving...")
    save_grid(grid_file_out_abs, grid_in)

  logger.info(f"Done. Written output to: {grid_folder_out}")
