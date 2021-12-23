from argparse import ArgumentParser
from logging import getLogger
from pathlib import Path
from typing import Iterable, List, Optional, cast

from textgrid_tools.app.globals import DEFAULT_N_DIGITS
from textgrid_tools.app.helper import get_grid_files, load_grid, save_grid
from textgrid_tools.core.mfa.interval_boundary_adjustment import (
    can_fix_interval_boundaries_grid, fix_interval_boundaries_grid)
from tqdm import tqdm


def init_files_fix_boundaries_parser(parser: ArgumentParser):
  parser.description = "This command set the closest boundaries of tiers to those of a reference tier."
  parser.add_argument("--grid_folder_in", type=Path, required=True)
  parser.add_argument("--reference_tier", type=str, required=True)
  parser.add_argument("--difference_threshold", type=float, required=False)
  parser.add_argument("--n_digits", type=int, default=DEFAULT_N_DIGITS)
  parser.add_argument("--target_tiers", type=str, nargs="+", required=True)
  parser.add_argument("--grid_folder_out", type=Path, required=True)
  parser.add_argument("--overwrite", action="store_true")
  return files_fix_boundaries


def files_fix_boundaries(grid_folder_in: Path, reference_tier: str, difference_threshold: Optional[float], n_digits: int, target_tiers: List[str], grid_folder_out: Path, overwrite: bool) -> None:
  logger = getLogger(__name__)

  if not grid_folder_in.exists():
    logger.error("Textgrid folder does not exist!")
    return

  grid_files = get_grid_files(grid_folder_in)
  logger.info(f"Found {len(grid_files)} grid files.")

  success = True
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
    can_fix = can_fix_interval_boundaries_grid(
      grid_in, reference_tier, target_tiers, difference_threshold)
    if not can_fix:
      logger.info("Skipped.")
      success = False
      continue

    fixed_all = fix_interval_boundaries_grid(
      grid_in, reference_tier, target_tiers, difference_threshold)
    success &= fixed_all

    logger.info("Saving...")
    save_grid(grid_file_out_abs, grid_in)

  if success:
    logger.info("Done. Everything was successfully fixed!")
  else:
    logger.info("Done. Not everything was successfully fixed!")
  logger.info(f"Done. Written output to: {grid_folder_out}")
