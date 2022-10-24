from argparse import ArgumentParser, Namespace
from logging import getLogger
from pathlib import Path
from typing import List, cast

from textgrid import TextGrid
from tqdm import tqdm

from textgrid_tools.grids.stats_generation import print_stats
from textgrid_tools_cli.globals import ExecutionResult
from textgrid_tools_cli.helper import (add_directory_argument, add_encoding_argument,
                                       add_overwrite_argument, get_grid_files, parse_path,
                                       try_load_grid)
from textgrid_tools_cli.logging_configuration import get_file_logger, init_and_get_console_logger
from textgrid_tools_cli.validation import FileAlreadyExistsError


def get_grids_plot_stats_parser(parser: ArgumentParser):
  parser.description = "This command creates a violin plot of the all grids and exports marks statistics."
  add_directory_argument(parser)
  parser.add_argument("plot_output", type=parse_path, metavar="PLOT-OUTPUT",
                      help="path to output the generated diagram (*.png or *.pdf)")
  parser.add_argument("marks_output", type=parse_path, metavar="MARKS-OUTPUT",
                      help="path to output the generated marks statistics CSV file")
  add_encoding_argument(parser)
  add_overwrite_argument(parser)
  return app_plot_stats


def app_plot_stats(ns: Namespace) -> ExecutionResult:
  logger = init_and_get_console_logger(__name__)
  flogger = get_file_logger()

  grid_files = get_grid_files(ns.directory)

  if ns.plot_output.suffix.lower() not in {".png", ".pdf"}:
    logger.error("Only .png and .pdf outputs are supported!")
    return False, False

  if ns.marks_output.suffix.lower() not in {".csv"}:
    logger.error("Only .csv outputs are supported!")
    return False, False

  if not ns.overwrite and (error := FileAlreadyExistsError.validate(ns.plot_output)):
    logger.error(error.default_message)
    return False, False

  if not ns.overwrite and (error := FileAlreadyExistsError.validate(ns.marks_output)):
    logger.error(error.default_message)
    return False, False

  grids: List[TextGrid] = []
  for file_nr, (file_stem, rel_path) in enumerate(tqdm(grid_files.items()), start=1):
    flogger.info(f"Processing {file_stem}")
    grid_file_in_abs = ns.directory / rel_path
    error, grid = try_load_grid(grid_file_in_abs, ns.encoding)

    if error:
      flogger.debug(error.exception)
      flogger.error(error.default_message)
      return False, False
    assert grid is not None

    grids.append(grid)

  (error, _), figure, marks = print_stats(grids, logger)

  success = error is None

  if not success:
    logger.error(error.default_message)
    return False, False

  ns.plot_output.parent.mkdir(parents=True, exist_ok=True)
  getLogger('matplotlib.backends.backend_pdf').disabled = True
  try:
    figure.savefig(ns.plot_output)
  except Exception as ex:
    logger.error("Saving of plot was not successful!")
    logger.debug(ex)
    return False, False
  getLogger('matplotlib.backends.backend_pdf').disabled = False

  ns.marks_output.parent.mkdir(parents=True, exist_ok=True)
  try:
    cast(Path, ns.marks_output).write_text(marks, "UTF-8")
  except Exception as ex:
    logger.error("Saving of marks statistics was not successful!")
    logger.debug(ex)
    return False, True

  logger.info(f"Exported plot to: \"{ns.plot_output.absolute()}\".")
  logger.info(f"Exported marks statistics to: \"{ns.marks_output.absolute()}\".")

  return True, True
