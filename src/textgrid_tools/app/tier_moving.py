from argparse import ArgumentParser
from logging import getLogger
from pathlib import Path
from typing import Iterable, List, cast

from textgrid_tools.app.globals import DEFAULT_N_DIGITS
from textgrid_tools.app.helper import get_grid_files, load_grid, save_grid
from textgrid_tools.core.mfa.tier_moving import can_move_tier, move_tier
from tqdm import tqdm


def init_files_move_tier_parser(parser: ArgumentParser):
  parser.description = "This commands moves a tier to another position in the grid."
  parser.add_argument("--grid_folder_in", type=Path, required=True)
  parser.add_argument("--tier", type=str, required=True)
  parser.add_argument("--position", type=int, required=True)
  parser.add_argument("--n_digits", type=int, default=DEFAULT_N_DIGITS)
  parser.add_argument("--grid_folder_out", type=Path, required=True)
  parser.add_argument("--overwrite", action="store_true")
  return files_move_tier


def files_move_tier(grid_folder_in: Path, tier: str, position: int, n_digits: int, grid_folder_out: Path, overwrite: bool) -> None:
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
    can_move = can_move_tier(grid_in, tier, position)
    if not can_move:
      logger.info("Skipped.")
      continue

    changed_anything = move_tier(grid_in, tier, position)

    if not changed_anything:
      logger.info("Didn't changed anything.")

    logger.info("Saving...")
    save_grid(grid_file_out_abs, grid_in)

  logger.info(f"Done. Written output to: {grid_folder_out}")
