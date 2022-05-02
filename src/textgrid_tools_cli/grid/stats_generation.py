from argparse import ArgumentParser
from logging import getLogger
from pathlib import Path

from textgrid_tools import print_stats
from textgrid_tools_cli.globals import ExecutionResult
from textgrid_tools_cli.helper import (add_directory_argument, add_n_digits_argument,
                                       get_grid_files, parse_positive_float, try_load_grid)


def get_stats_generation_parser(parser: ArgumentParser):
  parser.description = "This command generate statistics about the grid files."
  add_directory_argument(parser)
  parser.add_argument("--duration-threshold", type=parse_positive_float, default=0.002,
                      help="warn at intervals smaller than this duration (in seconds)")
  add_n_digits_argument(parser)
  return app_print_stats


def app_print_stats(directory: Path, duration_threshold: float, n_digits: int) -> ExecutionResult:
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

    error, changed_anything = print_stats(grid, duration_threshold)
    logger.info("")
    assert not changed_anything
    success = error is None
    total_success &= success

    if not success:
      logger.error(error.default_message)
      logger.info("Skipped.")
      continue

  return total_success, True