from argparse import ArgumentParser, Namespace
from logging import getLogger
from typing import List

from textgrid import TextGrid
from tqdm import tqdm

from textgrid_tools.grids.durations_plotting import plot_grids_interval_durations_diagram
from textgrid_tools_cli.globals import ExecutionResult
from textgrid_tools_cli.helper import (add_directory_argument, add_encoding_argument,
                                       add_tiers_argument, get_grid_files, parse_path,
                                       try_load_grid)
from textgrid_tools_cli.logging_configuration import get_file_logger, init_and_get_console_logger


def get_grids_plot_interval_durations_parser(parser: ArgumentParser):
  parser.description = "This command creates a violin plot of the interval durations of all grids."
  add_directory_argument(parser)
  add_tiers_argument(parser, "tiers containing the intervals that should be plotted")
  parser.add_argument("output", type=parse_path, metavar="OUTPUT",
                      help="path to output the generated diagram (*.png or *.pdf)")
  add_encoding_argument(parser)
  return app_plot_interval_durations


def app_plot_interval_durations(ns: Namespace) -> ExecutionResult:
  logger = init_and_get_console_logger(__name__)
  flogger = get_file_logger()

  grid_files = get_grid_files(ns.directory)

  if ns.output.suffix.lower() not in {".png", ".pdf"}:
    logger.error("Only .png and .pdf outputs are supported!")
    return False, False

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

  (error, _), figure = plot_grids_interval_durations_diagram(grids, ns.tiers, flogger)

  success = error is None

  if not success:
    logger.error(error.default_message)
    return False, False

  ns.output.parent.mkdir(parents=True, exist_ok=True)
  getLogger('matplotlib.backends.backend_pdf').disabled = True
  figure.savefig(ns.output)
  getLogger('matplotlib.backends.backend_pdf').disabled = False

  logger.info(f"Exported plot to: \"{ns.output.absolute()}\".")

  return True, True
