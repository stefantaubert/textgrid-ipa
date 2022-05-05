from argparse import ArgumentParser, Namespace
from logging import getLogger
from pathlib import Path
from typing import List, Optional

from textgrid.textgrid import TextGrid

from textgrid_tools.grids.marks_exporting import get_marks_txt
from textgrid_tools_cli.globals import ExecutionResult
from textgrid_tools_cli.helper import (add_directory_argument, add_encoding_argument,
                                       add_n_digits_argument, add_overwrite_argument,
                                       get_grid_files, get_optional, parse_non_empty,
                                       parse_non_empty_or_whitespace, parse_path, try_load_grid)
from textgrid_tools_cli.validation import FileAlreadyExistsError


def get_marks_exporting_parser(parser: ArgumentParser):
  parser.description = "This command exports all marks on a tier of all grids into one text file."
  add_directory_argument(parser)
  parser.add_argument("tier", type=parse_non_empty_or_whitespace,
                      help="tier containing the intervals that should be exported")
  parser.add_argument("output", type=parse_path, metavar="output",
                      help="path to output the marks (*.txt)")
  parser.add_argument("--sep", type=str,
                      help="separator for intervals in output", default="|")
  add_encoding_argument(parser, "output encoding")
  add_n_digits_argument(parser)
  add_overwrite_argument(parser)
  return app_plot_interval_durations


def app_plot_interval_durations(ns: Namespace) -> ExecutionResult:
  logger = getLogger(__name__)

  grid_files = get_grid_files(ns.directory)

  if ns.output.suffix.lower() not in {".txt"}:
    logger.error("Only .txt outputs are supported!")
    return False, False

  if not ns.overwrite and (error := FileAlreadyExistsError.validate(ns.output)):
    logger.error(error.default_message)
    return False, False

  grids: List[TextGrid] = []
  for file_nr, (file_stem, rel_path) in enumerate(grid_files.items(), start=1):
    logger.info(f"Reading {file_stem} ({file_nr}/{len(grid_files)})...")
    grid_file_in_abs = ns.directory / rel_path
    error, grid = try_load_grid(grid_file_in_abs, ns.n_digits)

    if error:
      logger.error(error.default_message)
      logger.info("Skipped.")
      continue
    assert grid is not None

    grids.append(grid)

  (error, _), txt = get_marks_txt(grids, ns.tier, ns.sep)

  success = error is None

  if not success:
    logger.error(error.default_message)
    return False, False

  ns.output.parent.mkdir(parents=True, exist_ok=True)
  ns.output.write_text(txt, ns.encoding)
  logger.info(f"Exported text to: {ns.output}")

  return True, False
