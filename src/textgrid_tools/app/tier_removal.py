from argparse import ArgumentParser
from logging import getLogger
from pathlib import Path
from typing import Iterable, List, cast

from textgrid_tools.app.helper import (add_n_digits_argument,
                                       add_overwrite_argument, get_grid_files,
                                       load_grid, save_grid)
from textgrid_tools.core.tier_removal import can_remove_tiers, remove_tiers
from tqdm import tqdm


def init_files_remove_tiers_parser(parser: ArgumentParser):
  parser.description = "This command removes tiers from a grid."
  parser.add_argument("directory", type=Path, metavar="directory",
                      help="the directory containing the grid files")
  parser.add_argument("tiers", metavar="tiers", type=str, nargs="+",
                      help="the tiers which should be removed")
  add_n_digits_argument(parser)
  parser.add_argument("--output-directory", metavar='PATH', type=Path,
                      help="the directory where to output the modified grid files if not to directory")
  add_overwrite_argument(parser)
  return files_remove_tiers


def files_remove_tiers(directory: Path, tiers: List[str], n_digits: int, output_directory: Path, overwrite: bool) -> None:
  logger = getLogger(__name__)

  if not directory.exists():
    logger.error("Textgrid folder does not exist!")
    return

  if output_directory is None:
    output_directory = directory

  tiers_set = set(tiers)
  if len(tiers_set) == 0:
    logger.error("Please specify at least one tier!")
    return

  grid_files = get_grid_files(directory)
  logger.info(f"Found {len(grid_files)} grid files.")

  logger.info("Reading files...")
  for file_stem in cast(Iterable[str], tqdm(grid_files)):
    logger.info(f"Processing {file_stem} ...")

    grid_file_out_abs = output_directory / grid_files[file_stem]

    if grid_file_out_abs.exists() and not overwrite:
      logger.info("Target grid already exists.")
      logger.info("Skipped.")
      continue

    grid_file_in_abs = directory / grid_files[file_stem]
    grid_in = load_grid(grid_file_in_abs, n_digits)

    can_remove = can_remove_tiers(grid_in, tiers_set)
    if not can_remove:
      logger.info("Skipped.")
      continue

    remove_tiers(grid_in, tiers_set)

    logger.info("Saving...")
    save_grid(grid_file_out_abs, grid_in)

  logger.info(f"Done. Written output to: {output_directory}")
