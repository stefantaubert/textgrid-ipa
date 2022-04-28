from argparse import ArgumentParser
from collections import Counter
from itertools import chain
from logging import getLogger
from pathlib import Path
from tempfile import gettempdir
from typing import Callable, List, Optional, Set, Tuple

from ordered_set import OrderedSet
from textgrid.textgrid import TextGrid

from textgrid_utils.grids.grid_merging import merge_grids
from textgrid_utils.helper import get_all_intervals
from textgrid_utils.validation import InvalidGridError, NotExistingTierError, ValidationError
from textgrid_utils_cli.common import getFileLogger, try_initFileLogger
from textgrid_utils_cli.globals import DEFAULT_N_DIGITS, ExecutionResult
from textgrid_utils_cli.helper import (add_directory_argument, add_encoding_argument,
                                       add_tiers_argument, get_grid_files, parse_path, save_grid,
                                       try_load_grid)


def get_grids_merging_parser(parser: ArgumentParser) -> Callable:
  parser.description = "This command merges grid files."
  default_log_path = Path(gettempdir()) / "textgrid-tools.log"
  add_directory_argument(parser)
  parser.add_argument("output", type=parse_path, metavar="output",
                      help="path to write the generated grid")
  parser.add_argument("--log", type=parse_path, metavar="FILE",
                      help="path to write the log", default=default_log_path)
  return merge_grids_app


def merge_grids_app(directory: Path, output: Path, log: Optional[Path]) -> ExecutionResult:
  logger = getLogger(__name__)
  if log is not None:
    try_initFileLogger(log)

  grid_files = get_grid_files(directory)

  grids: List[TextGrid] = []
  for file_nr, (file_stem, rel_path) in enumerate(grid_files.items(), start=1):
    if file_nr == 10:
      break
    logger.info(f"Reading {file_stem} ({file_nr}/{len(grid_files)})...")
    grid_file_in_abs = directory / rel_path
    error, grid = try_load_grid(grid_file_in_abs, DEFAULT_N_DIGITS)

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

  (error, changed_anything), merged_grid = merge_grids(grids)

  success = error is None

  if not success:
    logger.error(error.default_message)
    return False, False

  logger.info("Saving grid...")
  try:
    save_grid(output, merged_grid)
  except Exception as ex:
    logger.error("Grid couldn't be written!")
    logger.exception(ex)
    return False, False

  logger.info(f"Written grid to: {output.absolute()}")
  if log is not None:
    logger.info(f"Written log to: {log.absolute()}")

  return True, True
