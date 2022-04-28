from argparse import ArgumentParser
from logging import getLogger
from pathlib import Path

from ordered_set import OrderedSet
from textgrid_tools_cli.globals import ExecutionResult
from textgrid_tools_cli.helper import (ConvertToOrderedSetAction,
                                       add_directory_argument,
                                       add_n_digits_argument, get_grid_files,
                                       try_load_grid,
                                       parse_non_empty_or_whitespace,
                                       parse_positive_float)
from textgrid_tools_cli.validation import GridCouldNotBeLoadedError
from textgrid_tools.core import print_stats


def get_stats_generation_parser(parser: ArgumentParser):
  parser.description = "This command generate statistics about the grid files."
  add_directory_argument(parser)
  parser.add_argument("--duration-threshold", type=parse_positive_float, default=0.002,
                      help="warn at intervals smaller than this duration (in seconds)")
  parser.add_argument("--text-tiers", type=parse_non_empty_or_whitespace, nargs='*',
                      help="tiers with format TEXT which symbols should be printed", default=[], action=ConvertToOrderedSetAction)
  parser.add_argument("--spaced-tiers", type=parse_non_empty_or_whitespace, nargs='*',
                      help="tiers with format SPACED which symbols should be printed", default=[], action=ConvertToOrderedSetAction)
  add_n_digits_argument(parser)
  return app_print_stats


def app_print_stats(directory: Path, duration_threshold: float, text_tiers: OrderedSet[str], spaced_tiers: OrderedSet[str], n_digits: int) -> ExecutionResult:
  logger = getLogger(__name__)

  grid_files = get_grid_files(directory)

  total_success = True
  for file_nr, (file_stem, rel_path) in enumerate(grid_files.items(), start=1):
    logger.info(f"Statistics {file_stem} ({file_nr}/{len(grid_files)}):")

    grid_file_in_abs = directory / rel_path
    error, grid = try_load_grid(grid_file_in_abs, n_digits)

    if error:
      logger.error(error.default_message)
      logger.info("Skipped.")
      continue
    assert grid is not None

    error, changed_anything = print_stats(grid, duration_threshold, text_tiers, spaced_tiers)
    logger.info("")
    assert not changed_anything
    success = error is None
    total_success &= success

    if not success:
      logger.error(error.default_message)
      logger.info("Skipped.")
      continue

  return total_success, True
