from argparse import ArgumentParser
from logging import getLogger
from pathlib import Path
from typing import Iterable, Optional, cast

from textgrid_tools.app.helper import (add_n_digits_argument,
                                       add_overwrite_argument,
                                       add_overwrite_tier_argument,
                                       get_grid_files, load_grid, save_grid)
from textgrid_tools.core.mfa.tier_words_mapping import (can_map_words_to_tier,
                                                        map_words_to_tier)
from tqdm import tqdm


def init_files_map_words_to_tier_parser(parser: ArgumentParser):
  parser.description = "This command maps the content of a tier in one grid to a tier in another grid."
  parser.add_argument("reference_input_directory", metavar="reference-input-directory", type=Path,
                      help="the directory containing the grid files with the content that should be mapped")
  parser.add_argument("reference_tier", metavar="reference-tier", type=str,
                      help="the tier which should be mapped from")
  parser.add_argument("input_directory", type=Path, metavar="input-directory",
                      help="the directory containing the grid files which should be modified")
  parser.add_argument("tier", metavar="tier", type=str, help="the tier which should be modified")
  parser.add_argument("--output-tier", metavar="TIER", type=str, default=None,
                      help="the tier on which the mapped content should be written if not to tier.")
  add_n_digits_argument(parser)
  parser.add_argument("--output-directory", metavar='PATH', type=Path,
                      help="the directory where to output the modified grid files if not to input-directory")
  add_overwrite_tier_argument(parser)
  add_overwrite_argument(parser)
  return files_map_words_to_tier


def files_map_words_to_tier(input_directory: Path, tier: str, reference_input_directory: Path, reference_tier: str, new_tier: str, n_digits: int, output_directory: Optional[Path], overwrite_tier: bool, overwrite: bool) -> None:
  logger = getLogger(__name__)

  if not input_directory.exists():
    logger.error("Textgrid folder does not exist!")
    return

  if not reference_input_directory.exists():
    logger.error("Reference textgrid folder does not exist!")
    return

  if output_directory is None:
    output_directory = input_directory

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

  # if not path_align_dict.exists():
  #   logger.error("Alignment dictionary does not exist!")
  #   return

  # alignment_dict = parse_file(path_align_dict)

  logger.info("Reading files...")
  for file_stem in cast(Iterable[str], tqdm(common_files)):
    logger.info(f"Processing {file_stem} ...")

    grid_file_out_abs = output_directory / grid_files[file_stem]

    if grid_file_out_abs.exists() and not overwrite:
      logger.info("Target grids already exists.")
      logger.info("Skipped.")
      continue

    grid_file_in_abs = input_directory / grid_files[file_stem]
    grid_in = load_grid(grid_file_in_abs, n_digits)

  logger.info("Reading files...")
  for file_stem in cast(Iterable[str], tqdm(grid_files)):
    logger.info(f"Processing {file_stem} ...")

    grid_file_out_abs = output_directory / grid_files[file_stem]

    if grid_file_out_abs.exists() and not overwrite:
      logger.info("Target grid already exists.")
      logger.info("Skipped.")
      continue

    grid_file_in_abs = input_directory / grid_files[file_stem]
    grid_in = load_grid(grid_file_in_abs, n_digits)

    ref_grid_file_in_abs = reference_input_directory / ref_grid_files[file_stem]
    ref_grid_in = load_grid(ref_grid_file_in_abs, n_digits)

    can_map = can_map_words_to_tier(
      grid_in, tier, ref_grid_in, reference_tier, new_tier, overwrite_tier)
    if not can_map:
      logger.info("Skipped.")
      continue
    try:
      map_words_to_tier(grid_in, tier, ref_grid_in, reference_tier,
                        new_tier, overwrite_tier)
    except Exception as ex:
      logger.info("Skipped.")
      continue

    logger.info("Saving...")
    save_grid(grid_file_out_abs, grid_in)

  logger.info(f"Done. Written output to: {output_directory}")
