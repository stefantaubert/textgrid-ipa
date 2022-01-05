from argparse import ArgumentParser
from logging import getLogger
from pathlib import Path
from typing import Iterable, Optional, cast

from text_utils import StringFormat
from textgrid_tools.app.helper import (add_n_digits_argument,
                                       add_overwrite_argument,
                                       add_overwrite_tier_argument,
                                       get_grid_files, load_grid, save_grid)
from textgrid_tools.core.intervals.joining.non_pause_joining import (
    can_join_intervals, join_intervals)
from textgrid_tools.core.mfa.interval_format import IntervalFormat
from tqdm import tqdm


def init_files_join_intervals_on_non_pauses_parser(parser: ArgumentParser):
  parser.description = "This command joins adjacent intervals of a single tier to intervals containing sentences."
  parser.add_argument("directory", type=Path, metavar="directory",
                      help="directory containing the grid files")
  parser.add_argument("tier", type=str, help="the tier on which the intervals should be joined")
  add_n_digits_argument(parser)
  parser.add_argument('--mark-format', choices=StringFormat,
                      type=StringFormat.__getitem__, default=StringFormat.TEXT, help="format of marks in tier")
  parser.add_argument('--mark-type', choices=IntervalFormat,
                      type=IntervalFormat.__getitem__, default=IntervalFormat.WORD, help="type of marks in tier")
  parser.add_argument("--output-tier", metavar="TIER", type=str, default=None,
                      help="tier on which the mapped content should be written to if not to tier")
  parser.add_argument("--output-directory", metavar='PATH', type=Path,
                      help="directory where to output the modified grid files if not to directory")
  add_overwrite_tier_argument(parser)
  add_overwrite_argument(parser)
  return files_join_intervals_on_non_pauses


def files_join_intervals_on_non_pauses(directory: Path, tier: str, mark_format: StringFormat, mark_type: IntervalFormat, output_tier: Optional[str], overwrite_tier: bool, n_digits: int, output_directory: Path, overwrite: bool) -> None:
  logger = getLogger(__name__)

  if not directory.exists():
    logger.error(f"Directory \"{directory}\" does not exist!")
    return

  if output_directory is None:
    output_directory = directory

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

    can_join = can_join_intervals(grid_in, tier, output_tier, overwrite_tier)
    if not can_join:
      logger.info("Skipped.")
      continue

    join_intervals(grid_in, tier, mark_format, mark_type,
                   output_tier, overwrite_tier)

    logger.info("Saving...")
    save_grid(grid_file_out_abs, grid_in)

  logger.info(f"Done. Written output to: {output_directory}")
