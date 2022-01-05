from argparse import ArgumentParser
from logging import getLogger
from pathlib import Path
from typing import Iterable, Optional, cast

from textgrid_tools.app.helper import (add_n_digits_argument,
                                       add_overwrite_argument,
                                       add_overwrite_tier_argument,
                                       get_grid_files, load_grid, save_grid)
from textgrid_tools.core.mfa.tier_copying import can_copy, copy_tier_to_grid
from tqdm import tqdm


def init_files_copy_tier_to_grid_parser(parser: ArgumentParser):
  parser.description = "This command maps the content of a tier in one grid to a tier in another grid."
  parser.add_argument("reference_input_directory", metavar="reference-input-directory", type=Path,
                      help="the directory containing the grid files with the content that should be mapped")
  parser.add_argument("reference_tier", metavar="reference-tier", type=str,
                      help="the tier which should be mapped from")
  parser.add_argument("input_directory", type=Path, metavar="input-directory",
                      help="the directory containing the grid files which should be modified")
  parser.add_argument("--output-tier", metavar="TIER", type=str, default=None,
                      help="tier on which the mapped content should be written if not to reference-tier.")
  add_n_digits_argument(parser)
  parser.add_argument("--output-directory", metavar='PATH', type=Path,
                      help="the directory where to output the modified grid files if not to input-directory")
  add_overwrite_tier_argument(parser)
  add_overwrite_argument(parser)
  return files_copy_tier_to_grid


def files_copy_tier_to_grid(reference_input_directory: Path, reference_tier: str, input_directory: Path, output_tier: Optional[str], n_digits: int, output_directory: Optional[Path], overwrite_tier: bool, overwrite: bool) -> None:
  logger = getLogger(__name__)

  if not reference_input_directory.exists():
    logger.error("Reference textgrid folder does not exist!")
    return

  if not input_directory.exists():
    logger.error("Textgrid folder does not exist!")
    return

  if input_directory == reference_input_directory:
    logger.info("Please select two different directories!")
    return

  if output_directory is None:
    output_directory = input_directory

  if output_tier is None:
    output_tier = reference_tier

  grid_files = get_grid_files(input_directory)
  logger.info(f"Found {len(grid_files)} grid files.")

  ref_grid_files = get_grid_files(reference_input_directory)
  logger.info(f"Found {len(ref_grid_files)} reference grid files.")

  common_files = set(grid_files.keys()).intersection(ref_grid_files.keys())
  missing_grid_files = set(ref_grid_files.keys()).difference(grid_files.keys())
  missing_ref_grid_files = set(grid_files.keys()).difference(ref_grid_files.keys())

  logger.info(f"{len(missing_grid_files)} grid files missing.")
  logger.info(f"{len(missing_ref_grid_files)} reference grid files missing.")

  logger.info(f"Found {len(common_files)} matching files.")

  logger.info("Reading files...")
  for file_stem in cast(Iterable[str], tqdm(grid_files)):
    logger.info(f"Processing {file_stem} ...")

    grid_file_out_abs = output_directory / grid_files[file_stem]

    if grid_file_out_abs.exists() and not overwrite:
      logger.info("Target grid already exists.")
      logger.info("Skipped.")
      continue

    ref_grid_file_in_abs = reference_input_directory / ref_grid_files[file_stem]
    ref_grid_in = load_grid(ref_grid_file_in_abs, n_digits)

    grid_file_in_abs = input_directory / grid_files[file_stem]
    grid_in = load_grid(grid_file_in_abs, n_digits)

    can_copy_tier = can_copy(grid_in, ref_grid_in, reference_tier, output_tier, overwrite_tier)
    if not can_copy_tier:
      logger.info("Skipped.")
      continue

    copy_tier_to_grid(grid_in, ref_grid_in, reference_tier,
                      output_tier, overwrite_tier)

    logger.info("Saving...")
    save_grid(grid_file_out_abs, grid_in)

  logger.info(f"Done. Written output to: {output_directory}")
