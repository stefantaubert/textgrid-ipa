from argparse import ArgumentParser, Namespace
from logging import getLogger
from pathlib import Path
from tempfile import gettempdir
from typing import Callable, List

from textgrid import TextGrid

from textgrid_tools.grids.grid_merging import merge_grids
from textgrid_tools_cli.globals import ExecutionResult
from textgrid_tools_cli.helper import (add_directory_argument, get_grid_files, get_optional,
                                       parse_path, parse_positive_float, try_save_grid, try_load_grid)
from textgrid_tools_cli.logging_configuration import try_init_file_logger

from textgrid_tools_cli.helper import add_encoding_argument


def get_grids_merging_parser(parser: ArgumentParser) -> Callable:
  parser.description = "This command merges grid files."
  add_directory_argument(parser)
  parser.add_argument("output", type=parse_path, metavar="output",
                      help="path to write the generated grid")
  parser.add_argument("--insert-duration", type=get_optional(parse_positive_float),
                      help="insert an interval between subsequent grids having this duration and mark as content", default=None)
  parser.add_argument(
    "--insert-mark", type=str, help="set this mark in the inserted interval (only if insert-duration > 0)", default="")
  add_encoding_argument(parser)
  return merge_grids_app


def merge_grids_app(ns: Namespace) -> ExecutionResult:
  logger = getLogger(__name__)

  grid_files = get_grid_files(ns.directory)

  grids: List[TextGrid] = []
  for file_nr, (file_stem, rel_path) in enumerate(grid_files.items(), start=1):
    if file_nr == 10:
      break
    logger.info(f"Reading {file_stem} ({file_nr}/{len(grid_files)})...")
    grid_file_in_abs = ns.directory / rel_path
    error, grid = try_load_grid(grid_file_in_abs, ns.encoding)

    if error:
      logger.error(error.default_message)
      logger.info("Skipped.")
      continue
    assert grid is not None

    grids.append(grid)

  success = error is None

  if not success:
    logger.error(error.default_message)
    return False, False

  (error, changed_anything), merged_grid = merge_grids(grids, ns.insert_duration, ns.insert_mark)

  success = error is None

  if not success:
    logger.error(error.default_message)
    return False, False

  logger.info("Saving grid...")
  try:
    try_save_grid(ns.output, merged_grid, ns.encoding)
  except Exception as ex:
    logger.error("Grid couldn't be written!")
    logger.exception(ex)
    return False, False

  logger.info(f"Written grid to: {ns.output.absolute()}")

  return True, True
