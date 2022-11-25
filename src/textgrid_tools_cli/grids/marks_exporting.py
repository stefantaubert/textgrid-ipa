from argparse import ArgumentParser, Namespace
from typing import List

from textgrid import TextGrid
from tqdm import tqdm

from textgrid_tools.grids.marks_exporting import get_marks_txt
from textgrid_tools_cli.globals import ExecutionResult
from textgrid_tools_cli.helper import (add_directory_argument, add_encoding_argument,
                                       get_grid_files, parse_non_empty_or_whitespace,
                                       parse_txt_path, try_load_grid)
from textgrid_tools_cli.logging_configuration import get_file_logger, init_and_get_console_logger


def get_marks_exporting_parser(parser: ArgumentParser):
  parser.description = "This command exports all marks on a tier of all grids into one text file."
  add_directory_argument(parser)
  parser.add_argument("tier", type=parse_non_empty_or_whitespace, metavar="TIER",
                      help="tier containing the intervals that should be exported")
  parser.add_argument("output", type=parse_txt_path, metavar="OUTPUT",
                      help="path to output the marks (*.txt)")
  parser.add_argument("--sep", type=str, metavar="SEP",
                      help="separator for intervals in output", default="|")
  add_encoding_argument(parser, "encoding of input grid files and OUTPUT text file")
  return export_marks_ns


def export_marks_ns(ns: Namespace) -> ExecutionResult:
  logger = init_and_get_console_logger(__name__)
  flogger = get_file_logger()

  grid_files = get_grid_files(ns.directory)

  grids: List[TextGrid] = []
  # TODO all successful false on skipped files
  all_successful = True
  for file_nr, (file_stem, rel_path) in enumerate(tqdm(grid_files.items()), start=1):
    flogger.info(f"Processing {file_stem}")
    grid_file_in_abs = ns.directory / rel_path
    error, grid = try_load_grid(grid_file_in_abs, ns.encoding)

    if error:
      flogger.debug(error.exception)
      flogger.error(error.default_message)
      flogger.info("Skipped.")
      all_successful = False
      continue
    assert grid is not None

    grids.append(grid)

  (error, _), txt = get_marks_txt(grids, ns.tier, ns.sep, flogger)

  success = error is None

  if not success:
    logger.error(error.default_message)
    return False, False

  ns.output.parent.mkdir(parents=True, exist_ok=True)
  ns.output.write_text(txt, ns.encoding)
  logger.info(f"Exported text from {len(grids)} grid(s) to: \"{ns.output.absolute()}\".")

  return all_successful, True
