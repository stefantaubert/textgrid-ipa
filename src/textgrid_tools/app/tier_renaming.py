from argparse import ArgumentParser
from logging import getLogger
from pathlib import Path
from typing import Iterable, cast

from textgrid_tools.app.globals import DEFAULT_N_DIGITS
from textgrid_tools.app.helper import get_grid_files, load_grid
from textgrid_tools.core.mfa.tier_renaming import can_rename_tier, rename_tier
from tqdm import tqdm

# renames the first tier with the name


def init_files_rename_tier_parser(parser: ArgumentParser):
  parser.add_argument("--grid_folder_in", type=Path, required=True)
  parser.add_argument("--tier", type=str, required=True)
  parser.add_argument("--new_name", type=str, required=True)
  parser.add_argument("--n_digits", type=int, default=DEFAULT_N_DIGITS)
  parser.add_argument("--grid_folder_out", type=Path, required=True)
  parser.add_argument("--overwrite", action="store_true")
  return files_rename_tier


def files_rename_tier(grid_folder_in: Path, tier: str, new_name: str, n_digits: int, grid_folder_out: Path, overwrite: bool) -> None:
  logger = getLogger(__name__)

  if not grid_folder_in.exists():
    logger.error("Textgrid folder does not exist!")
    return

  if tier == new_name:
    logger.error("No different name was provided!")
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

    can_rename = can_rename_tier(grid_in, tier)
    if not can_rename:
      logger.info("Skipped.")
      continue

    rename_tier(grid_in, tier, new_name)

    logger.info("Saving...")
    grid_in.write(grid_file_out_abs)

  logger.info(f"Done. Written output to: {grid_folder_out}")
