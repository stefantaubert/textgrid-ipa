from argparse import ArgumentParser
from logging import getLogger
from pathlib import Path
from typing import Optional

from ordered_set import OrderedSet
from textgrid_utils_cli.globals import ExecutionResult
from textgrid_utils_cli.helper import (ConvertToOrderedSetAction,
                                       add_directory_argument,
                                       add_n_digits_argument,
                                       add_overwrite_argument, get_grid_files,
                                       get_optional, try_load_grid,
                                       parse_non_empty_or_whitespace,
                                       parse_path)
from textgrid_utils import plot_interval_durations_diagram


def get_plot_interval_durations_parser(parser: ArgumentParser):
  parser.description = "This command creates a violin plot of the interval durations."
  add_directory_argument(parser)
  parser.add_argument("tiers", type=parse_non_empty_or_whitespace, nargs='+',
                      help="tiers containing the intervals that should be plotted", action=ConvertToOrderedSetAction)
  parser.add_argument("-out", "--output-directory", metavar='PATH', type=get_optional(parse_path),
                      help="directory where to output the plots if not to the same directory")
  add_n_digits_argument(parser)
  add_overwrite_argument(parser)
  return app_plot_interval_durations


def app_plot_interval_durations(directory: Path, tiers: OrderedSet[str], output_directory: Optional[Path], n_digits: int, overwrite: bool) -> ExecutionResult:
  logger = getLogger(__name__)

  grid_files = get_grid_files(directory)

  if output_directory is None:
    output_directory = directory

  total_success = True
  for file_nr, (file_stem, rel_path) in enumerate(grid_files.items(), start=1):
    logger.info(f"Statistics {file_stem} ({file_nr}/{len(grid_files)}):")

    pdf_out = output_directory / f"{rel_path.stem}.pdf"
    png_out = output_directory / f"{rel_path.stem}.png"

    if not overwrite and (pdf_out.exists() or png_out.exists()):
      logger.info("Plot already exists. Skipping...")
      continue

    grid_file_in_abs = directory / rel_path
    error, grid = try_load_grid(grid_file_in_abs, n_digits)

    if error:
      logger.error(error.default_message)
      logger.info("Skipped.")
      continue
    assert grid is not None

    (error, changed_anything), figure = plot_interval_durations_diagram(grid, tiers)
    assert not changed_anything
    success = error is None
    total_success &= success

    if not success:
      logger.error(error.default_message)
      logger.info("Skipped.")
      continue

    output_directory.mkdir(parents=True, exist_ok=True)
    getLogger('matplotlib.backends.backend_pdf').disabled = True
    figure.savefig(pdf_out)
    getLogger('matplotlib.backends.backend_pdf').disabled = False
    figure.savefig(png_out)

  return total_success, False
