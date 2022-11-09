import math
from argparse import ArgumentParser, Namespace
from collections import OrderedDict
from pathlib import Path
from typing import Dict, List
from typing import OrderedDict as OrderedDictType

from ordered_set import OrderedSet
from textgrid import TextGrid
from tqdm import tqdm

from textgrid_tools.grids.durations_labelling import label_durations
from textgrid_tools_cli.globals import ExecutionResult
from textgrid_tools_cli.helper import (GRID_FILE_TYPE, ConvertToOrderedSetAction,
                                       add_directory_argument, add_encoding_argument,
                                       add_overwrite_argument, get_files_in_folder, get_grid_files,
                                       get_subfolders, parse_non_empty_or_whitespace,
                                       parse_non_negative_float, parse_positive_integer,
                                       try_load_grid, try_save_grid)
from textgrid_tools_cli.logging_configuration import get_file_logger, init_and_get_console_logger


def get_grids_label_durations_parser(parser: ArgumentParser):
  parser.description = "This command assigns a mark for each interval having a specific duration."
  add_directory_argument(parser)
  parser.add_argument("tier", type=parse_non_empty_or_whitespace, metavar="TIER",
                      help="tier containing the intervals which durations should be considered")
  parser.add_argument("assign_tier", type=parse_non_empty_or_whitespace, metavar="ASSIGN-TIER",
                      help="tier containing the intervals that should be marked; can also be equal to TIER")
  parser.add_argument("assign", type=str, metavar="MARK",
                      help="mark that should be assigned to the matching intervals")
  parser.add_argument("--range-mode", type=str, choices=["percent", "percentile", "absolute"],
                      metavar="RANGE-MODE", help="calculation on how interval duration boundaries are matched: percent -> calculate percent of maximum duration; percentile -> calculate percentile; absolute -> take absolute value", default="percentile")
  parser.add_argument("--marks-mode", type=str, choices=["separate", "all"],
                      metavar="MARKS-MODE", help="defines how the duration boundaries should be matched: separate -> for each mark only intervals with that mark will be considered; all -> all intervals will be considered together", default="percentile")
  parser.add_argument("--scope", type=str, choices=["file", "folder", "all"],
                      metavar="SCOPE", help="scope if RANGE-MODE is not absolute: file -> consider each file for it self; folder -> consider all files of the subfolders together; all -> consider all files together", default="all")
  parser.add_argument("--selection", type=str, metavar="MARK", nargs="*",
                      help="consider only intervals containing these marks; if not specified, all intervals will be considered", default=OrderedSet(), action=ConvertToOrderedSetAction)
  parser.add_argument("--range-min", type=parse_non_negative_float, metavar="MIN-VALUE",
                      help="inclusive minimum; on percent/percentile in range [0, 100]", default=0)
  parser.add_argument("--range-max", type=parse_non_negative_float, metavar="MAX-VALUE",
                      help="exclusive maximum; on percent/percentile in range (0, inf)", default=math.inf)
  parser.add_argument("--min-count", type=parse_positive_integer, metavar="MIN-COUNT",
                      help="minimum count of a mark to occur before MARK will be assigned if RANGE-MODE is not absolute: on MARKS-MODE \"separate\" -> each mark is counted independently; on MARKS-MODE \"all\": all marks are counted together. This is useful if a mark only occurs once and MAX-VALUE is \"inf\" and in that case the mark should not be assigned then MIN-COUNT could be set to \"2\".", default=1)
  add_encoding_argument(parser)
  add_overwrite_argument(parser)
  # add_output_directory_argument(parser)
  return app_label_durations


def app_label_durations(ns: Namespace) -> ExecutionResult:
  logger = init_and_get_console_logger(__name__)
  flogger = get_file_logger()

  resulting_files = (f for f in get_files_in_folder(
    ns.directory) if f.suffix.lower() == GRID_FILE_TYPE.lower())
  resulting_files = OrderedDict(sorted(
    (str(file.relative_to(ns.directory).parent / file.stem), file.relative_to(ns.directory))
      for file in resulting_files
  ))

  grids_to_groups: Dict[str, OrderedDictType[str, Path]] = {}
  if len(resulting_files) > 0:
    grids_to_groups[None] = resulting_files

  for subfolder in get_subfolders(ns.directory):
    subfolder_name = subfolder.relative_to(ns.directory)
    assert subfolder_name not in grids_to_groups
    grids_to_groups[subfolder_name] = get_grid_files(subfolder)

  loaded_grids: Dict[str, List[TextGrid]] = {}
  logger.info("Reading files...")
  for group_name, grids in tqdm(grids_to_groups.items()):
    for file_nr, (file_stem, rel_path) in enumerate(grids.items(), start=1):
      flogger.info(f"Processing {file_stem}")
      if group_name is None:
        grid_file_in_abs = ns.directory / rel_path
      else:
        grid_file_in_abs = ns.directory / group_name / rel_path
      error, grid = try_load_grid(grid_file_in_abs, ns.encoding)

      if error:
        flogger.debug(error.exception)
        flogger.error(error.default_message)
        flogger.info("Skipped.")
        continue
      assert grid is not None

      if group_name not in loaded_grids:
        loaded_grids[group_name] = []

      loaded_grids[group_name].append(grid)

  error, changed_anything = label_durations(loaded_grids, ns.tier, ns.assign_tier, ns.assign,
                                            ns.scope, ns.selection, ns.range_mode, ns.marks_mode, ns.range_min, ns.range_max, ns.min_count, flogger)

  success = error is None

  if not success:
    logger.error(error.default_message)
    return False, False

  logger.info("Applied operations successfully.")

  all_successful = True
  changed_any_file = False
  if changed_anything:
    for group_name, grids in loaded_grids.items():
      grids_changed = changed_anything[group_name]
      paths = grids_to_groups[group_name].values()
      for grid, grid_changed, rel_path in zip(grids, grids_changed, paths):
        if group_name is None:
          grid_file_in_abs = ns.directory / rel_path
        else:
          grid_file_in_abs = ns.directory / group_name / rel_path
        if grid_changed:
          changed_any_file = True
          error = try_save_grid(grid_file_in_abs, grid, ns.encoding)
          if error:
            logger.debug(error.exception)
            logger.error(error.default_message)
            all_successful = False
            continue
  return all_successful, changed_any_file
