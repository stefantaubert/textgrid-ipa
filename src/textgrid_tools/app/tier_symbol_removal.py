from argparse import ArgumentParser
from logging import getLogger
from pathlib import Path
from typing import Iterable, List, cast

from textgrid_tools.app.globals import DEFAULT_N_DIGITS
from textgrid_tools.app.helper import get_grid_files, load_grid, save_grid
from textgrid_tools.core.mfa.tier_symbol_removal import (can_remove_symbols,
                                                         remove_symbols)
from tqdm import tqdm


def init_remove_symbols_from_tiers_parser(parser: ArgumentParser):
  parser.description = "This command removes symbols from tiers."
  parser.add_argument("--grid_folder_in", type=Path, required=True)
  parser.add_argument("--tiers", type=str, nargs='+', required=True)
  parser.add_argument("--symbols", type=str, nargs='+', required=True)
  parser.add_argument("--n_digits", type=int, default=DEFAULT_N_DIGITS)
  parser.add_argument("--grid_folder_out", type=Path, required=True)
  parser.add_argument("--overwrite", action="store_true")
  return remove_symbols_from_tiers


def remove_symbols_from_tiers(grid_folder_in: Path, tiers: List[str], symbols: List[str], n_digits: int, grid_folder_out: Path, overwrite: bool) -> None:
  logger = getLogger(__name__)

  if not grid_folder_in.exists():
    logger.error("Textgrid folder does not exist!")
    return

  tiers_set = set(tiers)
  if len(tiers_set) == 0:
    logger.error("Please specify at least one tier!")
    return

  symbols_set = set(symbols)
  if len(symbols_set) == 0:
    logger.error("Please specify at least one symbol!")
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

    can_remove = can_remove_symbols(grid_in, tiers_set, symbols)
    if not can_remove:
      logger.info("Skipped.")
      continue

    changed_anything = remove_symbols(grid_in, tiers_set, symbols)

    if not changed_anything:
      logger.info("Nothing was changed.")

    logger.info("Saving...")
    save_grid(grid_file_out_abs, grid_in)

  logger.info(f"Done. Written output to: {grid_folder_out}")
