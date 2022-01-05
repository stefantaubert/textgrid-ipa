from argparse import ArgumentParser
from logging import getLogger
from pathlib import Path
from typing import Iterable, Optional, cast

from text_utils.string_format import StringFormat
from textgrid_tools.app.helper import (add_n_digits_argument,
                                       add_overwrite_argument,
                                       add_overwrite_tier_argument,
                                       get_grid_files, load_grid, save_grid)
from textgrid_tools.app.validation import validation_directory_exists_fails
from textgrid_tools.core.globals import ExecutionResult
from textgrid_tools.core.mfa.interval_format import IntervalFormat
from textgrid_tools.core.mfa.tier_mapping import map_tier_to_other_tier
from textgrid_tools.core.validation import Success
from tqdm import tqdm


def init_files_map_tier_to_other_tier_parser(parser: ArgumentParser):
  parser.description = "This command maps the content of a tier to another tier while ignoring pause-intervals."
  parser.add_argument("directory", type=Path, metavar="directory",
                      help="directory containing the grid files which should be modified")
  parser.add_argument("tier", metavar="tier", type=str,
                      help="tier which should be mapped")
  parser.add_argument("target_tier", metavar="target-tier",
                      type=str, help="tier which should be modified")
  parser.add_argument("--output-tier", metavar="TIER", type=str, default=None,
                      help="tier on which the mapped content should be written if not to target-tier.")
  parser.add_argument('--tier-format', choices=StringFormat,
                      type=StringFormat.__getitem__, default=StringFormat.TEXT)
  parser.add_argument('--target-tier-format', choices=StringFormat,
                      type=StringFormat.__getitem__, default=StringFormat.TEXT)
  parser.add_argument('--tiers-type', choices=IntervalFormat,
                      type=IntervalFormat.__getitem__, default=IntervalFormat.WORD)
  add_n_digits_argument(parser)
  parser.add_argument("--output-directory", metavar='PATH', type=Path,
                      help="the directory where to output the modified grid files if not to input-directory")
  add_overwrite_tier_argument(parser)
  add_overwrite_argument(parser)
  return files_map_tier_to_other_tier


def files_map_tier_to_other_tier(directory: Path, tier: str, tier_format: StringFormat, tiers_type: IntervalFormat, target_tier: str, target_tier_format: StringFormat, output_tier: Optional[str], n_digits: int, output_directory: Optional[Path], overwrite_tier: bool, overwrite: bool) -> ExecutionResult:
  logger = getLogger(__name__)

  if validation_directory_exists_fails(directory):
    return False

  if output_directory is None:
    output_directory = directory

  grid_files = get_grid_files(directory)
  logger.info(f"Found {len(grid_files)} grid files.")

  logger.info("Reading files...")
  total_success = True
  total_changed_anything = False
  for file_stem in cast(Iterable[str], tqdm(grid_files)):
    logger.info(f"Processing {file_stem} ...")

    grid_file_out_abs = output_directory / grid_files[file_stem]

    if grid_file_out_abs.exists() and not overwrite:
      logger.info("Target grid already exists.")
      logger.info("Skipped.")
      continue

    grid_file_in_abs = directory / grid_files[file_stem]
    grid_in = load_grid(grid_file_in_abs, n_digits)

    success, changed_anything = map_tier_to_other_tier(
      grid_in, tier, tier_format, tiers_type, target_tier,
        target_tier_format, output_tier, overwrite_tier
    )

    total_success &= success
    total_changed_anything |= changed_anything

    if not success:
      logger.info("Skipped.")
      continue

    logger.info("Saving...")
    save_grid(grid_file_out_abs, grid_in)

  logger.info(f"Written output to: \"{output_directory}\".")
  return total_success, changed_anything
