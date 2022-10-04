import os
from argparse import ArgumentParser, Namespace
from logging import getLogger
from pathlib import Path
from typing import Dict, Iterable, List, cast

from textgrid import TextGrid
from tqdm import tqdm

from textgrid_tools.grids.durations_labelling import label_durations
from textgrid_tools.grids.durations_plotting import plot_grids_interval_durations_diagram
from textgrid_tools_cli.globals import ExecutionResult
from textgrid_tools_cli.helper import (GRID_FILE_TYPE, ConvertToOrderedSetAction,
                                       add_directory_argument, add_encoding_argument,
                                       add_overwrite_argument, get_files_in_folder, get_grid_files,
                                       get_subfolders, parse_non_empty_or_whitespace, parse_path,
                                       try_load_grid)
from textgrid_tools_cli.logging_configuration import get_file_logger, init_and_get_console_logger
from textgrid_tools_cli.validation import FileAlreadyExistsError


def get_grids_label_durations_parser(parser: ArgumentParser):
  parser.description = "This command assigns a mark for each interval having a specific duration."
  add_directory_argument(parser)
  parser.add_argument("tier", type=parse_non_empty_or_whitespace,
                      help="tier containing the intervals that should be marked")
  add_encoding_argument(parser)
  add_overwrite_argument(parser)
  return app_label_durations


def app_label_durations(ns: Namespace) -> ExecutionResult:
  logger = init_and_get_console_logger(__name__)
  flogger = get_file_logger()

  grid_files = get_grid_files(ns.directory)

  _, subfolders, subfiles = os.walk(ns.directory)
  subfolders: Iterable[Path] = (ns.directory / f for f in subfolders)
  subfiles: Iterable[Path] = (ns.directory / f for f in subfiles)

  resulting_files = list(f for f in get_files_in_folder(
    ns.directory) if f.suffix.lower() == GRID_FILE_TYPE)

  grids: Dict[str, List[TextGrid]] = {}
  if len(resulting_files) > 0:
    grids[None] = resulting_files

  grids2: Dict[str, List[TextGrid]] = {}
  for subfolder in get_subfolders(ns.directory):
    subfolder_name = subfolder.relative_to(ns.directory)
    assert subfolder_name not in grids2
    grids2[subfolder_name] = get_grid_files(subfolder)

  loaded_grids: Dict[str, List[TextGrid]] = {}
  for group_name, grids in grids2.items():
    for file_nr, (file_stem, rel_path) in enumerate(tqdm(grids.items()), start=1):
      flogger.info(f"Processing {file_stem}")
      grid_file_in_abs = ns.directory / rel_path
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

  error, changed_anything = label_durations(loaded_grids, ns.tier, flogger)

  success = error is None

  if not success:
    logger.error(error.default_message)
    return False, False

  logger.info("Applied operations successfully.")
  if changed_anything:
    for _, grid in loaded_grids.items():
      error = try_save_grid(grid_file_out_abs, grid, encoding)
      if error:
        logger.debug(error.exception)
        logger.error(error.default_message)
        logger.debug(f"Duration (s): {perf_counter() - start}")
        return file_stem, (False, False, handler.records)
  return True, False
