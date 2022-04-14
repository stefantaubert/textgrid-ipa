from argparse import ArgumentParser
from collections import Counter
from itertools import chain
from logging import getLogger
from pathlib import Path
from tempfile import gettempdir
from typing import Callable, List, Optional, Set, Tuple

from ordered_set import OrderedSet
from textgrid.textgrid import TextGrid
from textgrid_tools.app.common import getFileLogger, try_initFileLogger
from textgrid_tools.app.globals import DEFAULT_N_DIGITS, ExecutionResult
from textgrid_tools.app.helper import (add_directory_argument,
                                       add_encoding_argument,
                                       add_tiers_argument, get_grid_files,
                                       parse_path, try_load_grid)
from textgrid_tools.core.helper import get_all_intervals
from textgrid_tools.core.validation import (InvalidGridError,
                                            NotExistingTierError,
                                            ValidationError)


def get_vocabulary_export_parser(parser: ArgumentParser) -> Callable:
  parser.description = "This command creates an vocabulary out of all words from multiple tiers in the grid files."
  default_log_path = Path(gettempdir()) / "textgrid-tools.log"
  add_directory_argument(parser)
  add_tiers_argument(parser, "tiers that contains the words as intervals")
  parser.add_argument("output", type=parse_path, metavar="output",
                      help="path to write the generated vocabulary")
  add_encoding_argument(parser, "vocabulary encoding")
  parser.add_argument("--log", type=parse_path, metavar="FILE",
                      help="path to write the log", default=default_log_path)
  return get_vocabulary_parsed


def get_vocabulary_parsed(directory: Path, tiers: OrderedSet[str], output: Path, encoding: str, log: Optional[Path]) -> ExecutionResult:
  logger = getLogger(__name__)
  if log is not None:
    try_initFileLogger(log)

  grid_files = get_grid_files(directory)

  grids: List[TextGrid] = []
  for file_nr, (file_stem, rel_path) in enumerate(grid_files.items(), start=1):
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

  error, vocabulary = get_vocabulary(grids, tiers)

  success = error is None

  if not success:
    logger.error(error.default_message)
    return False, False

  logger.info("Saving vocabulary...")
  vocabulary_txt = '\n'.join(vocabulary)
  try:
    output.write_text(vocabulary_txt, encoding)
  except:
    logger.error("Vocabulary couldn't be written!")
    return False, False

  logger.info(f"Written vocabulary to: {output.absolute()}")
  if log is not None:
    logger.info(f"Written log to: {log.absolute()}")

  return True, True


def get_vocabulary(grids: List[TextGrid], tier_names: Set[str]) -> Tuple[ValidationError, Optional[OrderedSet[str]]]:
  assert len(grids) > 0
  assert len(tier_names) > 0

  logger = getLogger(__name__)

  all_intervals = None
  for grid in grids:
    if error := InvalidGridError.validate(grid):
      return error, None

    for tier_name in tier_names:
      if error := NotExistingTierError.validate(grid, tier_name):
        return error, None

    intervals = get_all_intervals(grid, tier_names)
    if all_intervals is None:
      all_intervals = intervals
    else:
      all_intervals = chain(all_intervals, intervals)

  all_marks_counter = Counter(interval.mark for interval in all_intervals)
  flogger = getFileLogger()

  flogger.info("Occurrences:")
  total = sum(all_marks_counter.values())
  for mark, count in all_marks_counter.most_common():
    flogger.info(f"{mark}\t{count}x\t{count/total*100:.2f}%")

  all_marks = set(all_marks_counter.keys())
  if "" in all_marks:
    all_marks.remove("")
  logger.debug(f"Retrieved {len(all_marks)} unique marks.")
  result = OrderedSet(sorted(all_marks))
  return None, result
