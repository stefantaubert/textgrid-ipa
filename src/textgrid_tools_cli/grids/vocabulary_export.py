from argparse import ArgumentParser, Namespace
from collections import Counter
from itertools import chain
from logging import Logger
from typing import Callable, List, Optional, Set, Tuple

from ordered_set import OrderedSet
from textgrid import TextGrid
from tqdm import tqdm

from textgrid_tools.helper import get_all_intervals
from textgrid_tools.validation import InvalidGridError, NotExistingTierError, ValidationError
from textgrid_tools_cli.globals import ExecutionResult
from textgrid_tools_cli.helper import (add_directory_argument, add_encoding_argument,
                                       add_tiers_argument, get_grid_files, parse_path,
                                       try_load_grid)
from textgrid_tools_cli.logging_configuration import get_file_logger, init_and_get_console_logger


def get_vocabulary_export_parser(parser: ArgumentParser) -> Callable:
  parser.description = "This command creates an vocabulary out of all words from multiple tiers in the grid files."
  add_directory_argument(parser)
  add_tiers_argument(
    parser, "tiers that contains the words as intervals; must not contain line breaks")
  parser.add_argument("output", type=parse_path, metavar="OUTPUT",
                      help="path to write the generated vocabulary")
  parser.add_argument("--include-empty", action="store_true",
                      help="include empty marker in vocabulary if any occurs")
  add_encoding_argument(parser, "OUTPUT encoding")
  return get_vocabulary_parsed


def get_vocabulary_parsed(ns: Namespace) -> ExecutionResult:
  logger = init_and_get_console_logger(__name__)
  flogger = get_file_logger()

  grid_files = get_grid_files(ns.directory)

  grids: List[TextGrid] = []
  for file_nr, (file_stem, rel_path) in enumerate(tqdm(grid_files.items(), desc="Reading grids", unit=" file(s)"), start=1):
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

  error, vocabulary = get_vocabulary(grids, ns.tiers, ns.include_empty, flogger)

  success = error is None

  if not success:
    logger.error(error.default_message)
    return False, False

  any_word_contains_new_line = any("\n" in word for word in vocabulary)
  if any_word_contains_new_line:
    logger.warning("Some \"words\" contain line breaks, therefore the export does not contain each word on a new line! If you want to resolve this, remove the linebreaks from all intervals in the tiers you want to create a vocabulary from.")

  logger.info("Saving vocabulary...")
  vocabulary_txt = "\n".join(vocabulary)
  try:
    ns.output.write_text(vocabulary_txt, ns.encoding)
  except:
    logger.error("Vocabulary couldn't be written!")
    return False, False

  logger.info(f"Written vocabulary to: {ns.output.absolute()}")

  return True, True


def get_vocabulary(grids: List[TextGrid], tier_names: Set[str], include_empty: bool, logger: Logger) -> Tuple[ValidationError, Optional[OrderedSet[str]]]:
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
  all_marks_counter = Counter(interval.mark for interval in tqdm(
    all_intervals, desc="Parsing intervals", unit=" interval(s)"))
  flogger = get_file_logger()

  flogger.info("Occurrences:")
  total = sum(all_marks_counter.values())
  for mark, count in all_marks_counter.most_common():
    flogger.info(f"{mark}\t{count}x\t{count/total*100:.2f}%")

  all_marks = set(all_marks_counter.keys())
  if not include_empty and "" in all_marks:
    all_marks.remove("")
  logger.debug(f"Retrieved {len(all_marks)} unique marks.")
  result = OrderedSet(sorted(all_marks))
  return None, result
