from argparse import ArgumentParser
from logging import getLogger
from pathlib import Path
from typing import List

from textgrid_tools.app.globals import ExecutionResult
from textgrid_tools.app.helper import (ConvertToOrderedSetAction, add_grid_directory_argument,
                                       add_n_digits_argument, get_grid_files,
                                       load_grid, parse_non_empty_or_whitespace,
                                       parse_positive_float)
from textgrid_tools.app.validation import DirectoryNotExistsError
from textgrid_tools.core import print_stats


def get_stats_generation_parser(parser: ArgumentParser):
  parser.description = "This command generate statistics about the grid files."
  add_grid_directory_argument(parser)
  parser.add_argument("--duration-threshold", type=parse_positive_float, default=0.002,
                      help="warn at intervals smaller than this duration (in seconds)")
  parser.add_argument("--print-symbols-tiers", type=parse_non_empty_or_whitespace, nargs='*',
                      help="tiers with format SYMBOL which symbols should be printed", default=[], action=ConvertToOrderedSetAction)
  add_n_digits_argument(parser)
  return app_print_stats


def app_print_stats(directory: Path, duration_threshold: float, print_symbols_tiers: List[str], n_digits: int) -> ExecutionResult:
  logger = getLogger(__name__)

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

  return total_success, True
