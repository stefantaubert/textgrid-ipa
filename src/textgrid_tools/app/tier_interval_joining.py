from argparse import ArgumentParser
from logging import getLogger
from pathlib import Path
from typing import Iterable, Optional, cast

from textgrid_tools.app.helper import (add_n_digits_argument,
                                       add_overwrite_argument,
                                       add_overwrite_tier_argument,
                                       get_grid_files, load_grid, save_grid)
from textgrid_tools.core.mfa.string_format import StringFormat
from textgrid_tools.core.mfa.tier_interval_joining import (JoinMode,
                                                           can_join_intervals,
                                                           join_intervals)
from tqdm import tqdm


def init_files_join_intervals_parser(parser: ArgumentParser):
  parser.description = "This command joins adjacent intervals of a single tier."
  parser.add_argument("directory", type=Path, metavar="directory",
                      help="the directory containing the grid files")
  parser.add_argument("tier", type=str, help="the tier on which the intervals should be joined")
  add_n_digits_argument(parser)
  parser.add_argument('--mode', choices=JoinMode,
                      type=JoinMode.__getitem__, default=JoinMode.TIER, help="the mode which should be used for joining (TIER for joining all intervals on a tier together; BOUNDARY for joining intervals according to the interval boundaries of another tier; PAUSE for joining all intervals which are not separated by at least one empty interval that have a duration of at least 'pause')")
  parser.add_argument('--tier-format', choices=StringFormat,
                      type=StringFormat.__getitem__, default=StringFormat.TEXT, help="the text format of tier")
  parser.add_argument("--boundary-tier", type=str, metavar="TIER",
                      help="the tier from which the boundaries should be considered (only in mode BOUNDARY)")
  parser.add_argument("--pause", metavar="PAUSE", type=float,
                      help="the duration (seconds) an empty interval needs to have at least for it not to be joined together (only in mode PAUSE)")
  parser.add_argument("--output-tier", metavar="TIER", type=str, default=None,
                      help="the tier on which the mapped content should be written to if not to tier.")
  parser.add_argument("--output-directory", metavar='PATH', type=Path,
                      help="the directory where to output the modified grid files if not to input-directory")
  add_overwrite_tier_argument(parser)
  add_overwrite_argument(parser)
  return files_join_intervals


def files_join_intervals(directory: Path, tier: str, tier_format: StringFormat, mode: JoinMode, output_tier: Optional[str], pause: Optional[float], boundary_tier: Optional[str], overwrite_tier: bool, n_digits: int, output_directory: Path, overwrite: bool) -> None:
  logger = getLogger(__name__)

  if not directory.exists():
    logger.error(f"Directory \"{directory}\" does not exist!")
    return

  if output_directory is None:
    output_directory = directory

  if output_tier is None:
    output_tier = tier

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

    can_join = can_join_intervals(grid_in, tier, output_tier, pause,
                                  boundary_tier, mode, overwrite_tier)
    if not can_join:
      logger.info("Skipped.")
      continue

    join_intervals(grid_in, tier, tier_format, output_tier,
                   pause, boundary_tier, mode, overwrite_tier)

    logger.info("Saving...")
    save_grid(grid_file_out_abs, grid_in)

  logger.info(f"Done. Written output to: {output_directory}")
