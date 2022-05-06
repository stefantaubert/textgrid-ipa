from textgrid_tools_cli.logging_configuration import get_file_logger, init_and_get_console_logger
from argparse import ArgumentParser, Namespace
from collections import Counter
from itertools import chain
from logging import Logger
from typing import Callable, List, Optional, Set, Tuple

from ordered_set import OrderedSet
from textgrid import TextGrid

from textgrid_tools.helper import get_all_intervals
from textgrid_tools.validation import InvalidGridError, NotExistingTierError, ValidationError
from textgrid_tools_cli.globals import ExecutionResult
from textgrid_tools_cli.helper import (add_directory_argument, add_encoding_argument,
                                       add_tiers_argument, get_grid_files, parse_path,
                                       try_load_grid)
from textgrid_tools_cli.logging_configuration import get_file_logger


def get_vocabulary_export_parser(parser: ArgumentParser) -> Callable:
  parser.description = "This command creates an vocabulary out of all words from multiple tiers in the grid files."
  add_directory_argument(parser)
  add_tiers_argument(parser, "tiers that contains the words as intervals")
  parser.add_argument("output", type=parse_path, metavar="output",
                      help="path to write the generated vocabulary")
  add_encoding_argument(parser, "vocabulary encoding")
  return get_vocabulary_parsed


def get_vocabulary_parsed(ns: Namespace) -> ExecutionResult:
  logger = init_and_get_console_logger(__name__)
  flogger = get_file_logger()

  grid_files = get_grid_files(ns.directory)

  grids: List[TextGrid] = []
  for file_nr, (file_stem, rel_path) in enumerate(grid_files.items(), start=1):
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

  error, vocabulary = get_vocabulary(grids, ns.tiers, logger)

  success = error is None

  if not success:
    logger.error(error.default_message)
    return False, False

  logger.info("Saving vocabulary...")
  vocabulary_txt = '\n'.join(vocabulary)
  try:
    ns.output.write_text(vocabulary_txt, ns.encoding)
  except:
    logger.error("Vocabulary couldn't be written!")
    return False, False

  logger.info(f"Written vocabulary to: {ns.output.absolute()}")

  return True, True


def get_vocabulary(grids: List[TextGrid], tier_names: Set[str], logger: Logger) -> Tuple[ValidationError, Optional[OrderedSet[str]]]:
  assert len(grids) > 0
  assert len(tier_names) > 0

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
  flogger = get_file_logger()

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
