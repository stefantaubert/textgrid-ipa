from argparse import ArgumentParser, Namespace

from tqdm import tqdm

from textgrid_tools import print_stats
from textgrid_tools_cli.globals import ExecutionResult
from textgrid_tools_cli.helper import (add_directory_argument, add_encoding_argument,
                                       get_grid_files, parse_positive_float, try_load_grid)
from textgrid_tools_cli.logging_configuration import get_file_logger, init_and_get_console_logger


def get_stats_generation_parser(parser: ArgumentParser):
  parser.description = "This command generate statistics about the grid files."
  add_directory_argument(parser)
  parser.add_argument("--duration-threshold", type=parse_positive_float, default=0.002, metavar="THRESHOLD",
                      help="warn at intervals smaller than this duration (in seconds)")
  add_encoding_argument(parser)
  return app_print_stats


def app_print_stats(ns: Namespace) -> ExecutionResult:
  logger = init_and_get_console_logger(__name__)
  flogger = get_file_logger()

  grid_files = get_grid_files(ns.directory)

  logging_queues = dict.fromkeys(grid_files.keys())
  total_success = True
  for file_nr, (file_stem, rel_path) in enumerate(tqdm(grid_files.items()), start=1):
    flogger.info(f"Processing {file_stem}")
    grid_file_in_abs = ns.directory / rel_path
    error, grid = try_load_grid(grid_file_in_abs, ns.encoding)

    if error:
      flogger.debug(error.exception)
      flogger.error(error.default_message)
      flogger.info("Skipped.")
      continue
    assert grid is not None

    error, changed_anything = print_stats(grid, ns.duration_threshold, flogger)

    assert not changed_anything
    success = error is None
    total_success &= success

    if not success:
      flogger.error(error.default_message)
      flogger.info("Skipped.")
      continue

  return total_success, True
