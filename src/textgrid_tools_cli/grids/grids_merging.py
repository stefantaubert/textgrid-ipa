from argparse import ArgumentParser, Namespace
from typing import Callable, List

from textgrid import TextGrid
from tqdm import tqdm

from textgrid_tools.grids.grid_merging import merge_grids
from textgrid_tools_cli.globals import ExecutionResult
from textgrid_tools_cli.helper import (add_directory_argument, add_encoding_argument,
                                       get_grid_files, get_optional, parse_path,
                                       parse_positive_float, try_load_grid, try_save_grid)
from textgrid_tools_cli.logging_configuration import get_file_logger, init_and_get_console_logger


def get_grids_merging_parser(parser: ArgumentParser) -> Callable:
  parser.description = "This command merges grid files."
  add_directory_argument(parser)
  parser.add_argument("output", type=parse_path, metavar="OUTPUT",
                      help="file to write the generated grid (.TextGrid)")
  parser.add_argument("--insert-duration", type=get_optional(parse_positive_float), metavar="DURATION",
                      help="insert an interval between subsequent grids having this duration and mark as content", default=None)
  parser.add_argument(
    "--insert-mark", type=str, help="set this mark in the inserted interval (only if insert-duration > 0)", metavar="MARK", default="")
  add_encoding_argument(parser)
  return merge_grids_app


def merge_grids_app(ns: Namespace) -> ExecutionResult:
  logger = init_and_get_console_logger(__name__)
  flogger = get_file_logger()

  grid_files = get_grid_files(ns.directory)

  grids: List[TextGrid] = []
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

    grids.append(grid)

  success = error is None

  if not success:
    logger.error(error.default_message)
    return False, False

  (error, changed_anything), merged_grid = merge_grids(
    grids, ns.insert_duration, ns.insert_mark, flogger)

  success = error is None

  if not success:
    logger.error(error.default_message)
    return False, False

  logger.info("Saving grid...")
  error = try_save_grid(ns.output, merged_grid, ns.encoding)
  if error is not None:
    flogger.debug(error.exception)
    flogger.error(error.default_message)
    flogger.info("Skipped.")
    return False, False

  logger.info(f"Written grid to: {ns.output.absolute()}")

  return True, True
