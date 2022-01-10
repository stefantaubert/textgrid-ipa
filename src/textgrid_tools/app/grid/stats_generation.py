from argparse import ArgumentParser
from logging import getLogger
from pathlib import Path
from typing import List

from textgrid_tools.app.helper import (add_n_digits_argument, get_grid_files,
                                       load_grid)
from textgrid_tools.app.validation import DirectoryNotExistsError
from textgrid_tools.core import print_stats


def init_files_print_stats_parser(parser: ArgumentParser):
  parser.description = "This command generate statistics about the grid files."

  parser.add_argument("directory", type=Path, metavar="directory",
                      help="directory containing the grid files")
  parser.add_argument("--duration-threshold", type=float, default=0.002,
                      help="warn at intervals smaller than this duration")
  parser.add_argument("--print-symbols-tiers", type=str, nargs='*',
                      default="tiers with format SYMBOL which symbols should be printed")
  add_n_digits_argument(parser)
  return app_print_stats


def app_print_stats(directory: Path, duration_threshold: float, print_symbols_tiers: List[str], n_digits: int) -> None:
  logger = getLogger(__name__)

  if error := DirectoryNotExistsError.validate(directory):
    logger.error(error.default_message)
    return False, False

  grid_files = get_grid_files(directory)

  total_success = True
  for file_nr, (file_stem, rel_path) in enumerate(grid_files.items(), start=1):
    logger.info(f"Statistics {file_stem} ({file_nr}/{len(grid_files)}):")

    grid_file_in_abs = directory / rel_path
    grid_in = load_grid(grid_file_in_abs, n_digits)

    error, changed_anything = print_stats(grid_in, duration_threshold, set(print_symbols_tiers))
    logger.info("")
    assert not changed_anything
    success = error is None
    total_success &= success

    if not success:
      logger.error(error.default_message)
      logger.info("Skipped.")
      continue

  return total_success, False
