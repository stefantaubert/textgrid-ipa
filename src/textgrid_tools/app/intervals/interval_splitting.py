from argparse import ArgumentParser
from logging import getLogger
from pathlib import Path
from typing import Iterable, List, Optional, cast

from text_utils.string_format import StringFormat
from text_utils.types import Symbol
from textgrid_tools.app.globals import ExecutionResult
from textgrid_tools.app.helper import (add_n_digits_argument,
                                       add_overwrite_argument,
                                       add_overwrite_tier_argument, copy_grid,
                                       get_grid_files, load_grid, save_grid)
from textgrid_tools.app.validation import validation_directory_exists_fails
from textgrid_tools.core.intervals.splitting.interval_splitting import \
    split_intervals
from textgrid_tools.core.interval_format import IntervalFormat
from textgrid_tools.core.tier_mapping import map_tier_to_other_tier
from tqdm import tqdm


def init_files_split_intervals_parser(parser: ArgumentParser):
  parser.description = "This command maps the content of a tier to another tier while ignoring pause-intervals."
  parser.add_argument("directory", type=Path, metavar="directory",
                      help="directory containing the grid files which should be modified")
  parser.add_argument("tier", metavar="tier", type=str,
                      help="tier which should be mapped")
  parser.add_argument('--tier-format', choices=StringFormat,
                      type=StringFormat.__getitem__, default=StringFormat.TEXT)
  parser.add_argument('--tier-type', choices=IntervalFormat,
                      type=IntervalFormat.__getitem__, default=IntervalFormat.WORD)
  parser.add_argument('--join-symbols', type=str, nargs="*",
                      help="join these symbols while splitting WORD to SYMBOLS")
  parser.add_argument('--ignore-join-symbols', type=str, nargs="*",
                      help="don't join to these symbols while splitting WORD to SYMBOLS")
  add_n_digits_argument(parser)
  parser.add_argument("--output-tier", metavar="TIER", type=str, default=None,
                      help="tier on which the mapped content should be written if not to target-tier.")
  parser.add_argument("--output-directory", metavar='PATH', type=Path,
                      help="the directory where to output the modified grid files if not to input-directory")
  add_overwrite_tier_argument(parser)
  add_overwrite_argument(parser)
  return files_split_intervals_tier


def files_split_intervals_tier(directory: Path, tier: str, tier_format: StringFormat, tier_type: IntervalFormat, join_symbols: Optional[List[Symbol]], ignore_join_symbols: Optional[List[Symbol]], output_tier: Optional[str], n_digits: int, output_directory: Optional[Path], overwrite_tier: bool, overwrite: bool) -> ExecutionResult:
  logger = getLogger(__name__)

  if validation_directory_exists_fails(directory):
    return False

  if output_directory is None:
    output_directory = directory

  grid_files = get_grid_files(directory)
  logger.info(f"Found {len(grid_files)} grid files.")

  if join_symbols is not None:
    join_symbols = set(join_symbols)

  if ignore_join_symbols is not None:
    ignore_join_symbols = set(ignore_join_symbols)

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

    error, changed_anything = split_intervals(
      grid_in, tier, tier_format, tier_type, join_symbols, ignore_join_symbols, output_tier, overwrite_tier
    )

    if success := error is None:
      if changed_anything:
        save_grid(grid_file_out_abs, grid_in)
      elif directory != output_directory:
        copy_grid(grid_file_in_abs, grid_file_out_abs)
    else:
      logger.error(error.default_message)
      logger.info("Skipped.")

    total_success &= success
    total_changed_anything |= changed_anything

  logger.info(f"Written output to: \"{output_directory}\".")
  if not total_changed_anything:
    logger.info("Didn't changed anything.")
  if total_success:
    logger.info("Everything was successfull!")
  else:
    logger.warning("Not everything was successfull!")
  return total_success, changed_anything
