from argparse import ArgumentParser
from logging import getLogger
from pathlib import Path
from typing import Iterable, Optional, cast

from textgrid_tools.app.globals import DEFAULT_N_DIGITS
from textgrid_tools.app.helper import get_grid_files, load_grid, save_grid
from textgrid_tools.core.mfa.string_format import StringFormat
from textgrid_tools.core.mfa.tier_interval_joining import (JoinMode,
                                                           can_join_intervals,
                                                           join_intervals)
from tqdm import tqdm


def init_files_join_intervals_parser(parser: ArgumentParser):
  parser.add_argument("--grid_folder_in", type=Path, required=True)
  parser.add_argument("--tier", type=str, required=True)
  parser.add_argument("--n_digits", type=int, default=DEFAULT_N_DIGITS)
  parser.add_argument('--mode', choices=JoinMode,
                      type=JoinMode.__getitem__, required=True)
  parser.add_argument("--new_tier", type=str, required=True)
  parser.add_argument("--boundary_tier", type=str, required=False)
  parser.add_argument('--tier_string_format', choices=StringFormat,
                      type=StringFormat.__getitem__, default=StringFormat.TEXT)
  parser.add_argument("--min_pause_s", type=float, required=False)
  parser.add_argument("--grid_folder_out", type=Path, required=True)
  parser.add_argument("--overwrite_tier", action="store_true")
  parser.add_argument("--overwrite", action="store_true")
  return files_join_intervals


def files_join_intervals(grid_folder_in: Path, tier: str, tier_string_format: StringFormat, mode: JoinMode, new_tier: str, min_pause_s: Optional[float], boundary_tier: Optional[str], overwrite_tier: bool, n_digits: int, grid_folder_out: Path, overwrite: bool) -> None:
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

    can_join = can_join_intervals(grid_in, tier, new_tier, min_pause_s,
                                  boundary_tier, mode, overwrite_tier)
    if not can_join:
      logger.info("Skipped.")
      continue

    join_intervals(grid_in, tier, tier_string_format, new_tier,
                   min_pause_s, boundary_tier, mode, overwrite_tier)

    logger.info("Saving...")
    save_grid(grid_file_out_abs, grid_in)

  logger.info(f"Done. Written output to: {grid_folder_out}")
