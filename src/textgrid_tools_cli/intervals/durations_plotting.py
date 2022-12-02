from argparse import ArgumentParser, Namespace
from logging import getLogger

from tqdm import tqdm

from textgrid_tools import plot_interval_durations_diagram
from textgrid_tools_cli.globals import ExecutionResult
from textgrid_tools_cli.helper import (add_directory_argument, add_encoding_argument,
                                       add_overwrite_argument, add_tiers_argument, get_grid_files,
                                       get_optional, parse_path, try_load_grid)
from textgrid_tools_cli.logging_configuration import get_file_logger, init_and_get_console_logger


def get_plot_interval_durations_parser(parser: ArgumentParser):
  parser.description = "This command creates a violin plot of the interval durations."
  add_directory_argument(parser)
  add_tiers_argument(parser, "tiers containing the intervals that should be plotted")
  parser.add_argument("-out", "--output-directory", metavar='DIRECTORY', type=get_optional(parse_path),
                      help="directory where to output the plots if not to the same directory")
  add_encoding_argument(parser)
  add_overwrite_argument(parser)
  return app_plot_interval_durations


def app_plot_interval_durations(ns: Namespace) -> ExecutionResult:
  logger = init_and_get_console_logger(__name__)
  flogger = get_file_logger()

  grid_files = get_grid_files(ns.directory)

  output_directory = ns.output_directory
  if output_directory is None:
    output_directory = ns.directory

  total_success = True
  for file_nr, (file_stem, rel_path) in enumerate(tqdm(grid_files.items()), start=1):
    flogger.info(f"Processing \"{file_stem}\"")

    pdf_out = output_directory / f"{rel_path.stem}.pdf"
    png_out = output_directory / f"{rel_path.stem}.png"

    if not ns.overwrite and (pdf_out.exists() or png_out.exists()):
      flogger.info("Plot already exists. Skipping...")
      continue

    grid_file_in_abs = ns.directory / rel_path
    error, grid = try_load_grid(grid_file_in_abs, ns.encoding)

    if error:
      flogger.debug(error.exception)
      flogger.error(error.default_message)
      flogger.info("Skipped.")
      continue
    assert grid is not None

    (error, changed_anything), figure = plot_interval_durations_diagram(grid, ns.tiers, flogger)
    assert not changed_anything
    success = error is None
    total_success &= success

    if not success:
      flogger.error(error.default_message)
      flogger.info("Skipped.")
      continue

    output_directory.mkdir(parents=True, exist_ok=True)
    getLogger('matplotlib.backends.backend_pdf').disabled = True
    figure.savefig(pdf_out)
    getLogger('matplotlib.backends.backend_pdf').disabled = False
    figure.savefig(png_out)

  return total_success, True
