from argparse import ArgumentParser
from logging import getLogger
from pathlib import Path
from typing import List

from ordered_set import OrderedSet
from textgrid.textgrid import TextGrid
from textgrid_tools.app.globals import ExecutionResult
from textgrid_tools.app.helper import (ConvertToOrderedSetAction,
                                       add_directory_argument,
                                       add_n_digits_argument,
                                       add_overwrite_argument, get_grid_files,
                                       load_grid,
                                       parse_non_empty_or_whitespace,
                                       parse_path)
from textgrid_tools.app.validation import FileAlreadyExistsError
from textgrid_tools.core.grids.durations_plotting import \
    plot_grids_interval_durations_diagram


def get_grids_plot_interval_durations_parser(parser: ArgumentParser):
  parser.description = "This command creates a violin plot of the interval durations of all grids."
  add_directory_argument(parser)
  parser.add_argument("tiers", type=parse_non_empty_or_whitespace, nargs='+',
                      help="tiers containing the intervals that should be plotted", action=ConvertToOrderedSetAction)
  parser.add_argument("output", type=parse_path, metavar="output",
                      help="path to output the generated diagram (*.png or *.pdf)")
  add_n_digits_argument(parser)
  add_overwrite_argument(parser)
  return app_plot_interval_durations


def app_plot_interval_durations(directory: Path, tiers: OrderedSet[str], output: Path, n_digits: int, overwrite: bool) -> ExecutionResult:
  logger = getLogger(__name__)

  grid_files = get_grid_files(directory)

  if output.suffix.lower() not in {".png", ".pdf"}:
    logger.error("Only .png and .pdf outputs are supported!")
    return False, False

  if not overwrite and (error := FileAlreadyExistsError.validate(output)):
    logger.error(error.default_message)
    return False, False

  grids: List[TextGrid] = []
  for file_nr, (file_stem, rel_path) in enumerate(grid_files.items(), start=1):
    logger.info(f"Reading {file_stem} ({file_nr}/{len(grid_files)})...")
    grid_file_in_abs = directory / rel_path
    grid_in = load_grid(grid_file_in_abs, n_digits)
    grids.append(grid_in)

  (error, _), figure = plot_grids_interval_durations_diagram(grids, tiers)

  success = error is None

  if not success:
    logger.error(error.default_message)
    return False, False

  output.parent.mkdir(parents=True, exist_ok=True)
  getLogger('matplotlib.backends.backend_pdf').disabled = True
  figure.savefig(output)
  getLogger('matplotlib.backends.backend_pdf').disabled = False

  return True, False
