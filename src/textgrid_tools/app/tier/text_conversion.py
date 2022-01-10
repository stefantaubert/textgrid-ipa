from argparse import ArgumentParser
from logging import getLogger
from pathlib import Path
from typing import Optional

from text_utils import StringFormat
from textgrid_tools.app.globals import ExecutionResult
from textgrid_tools.app.helper import (add_n_digits_argument,
                                       add_overwrite_argument, get_grid_files,
                                       load_grid, save_text)
from textgrid_tools.app.validation import DirectoryNotExistsError
from textgrid_tools.core import convert_tier_to_text
from textgrid_tools.core.interval_format import IntervalFormat


def init_files_convert_grid_to_text_parser(parser: ArgumentParser):
  parser.description = "This command writes the content of a tier into a text file."

  parser.add_argument("directory", type=Path, metavar="directory",
                      help="directory containing the grids")
  parser.add_argument("tier", type=str, help="tier from which the text should be written")
  parser.add_argument('--tier-format', choices=StringFormat,
                      type=StringFormat.__getitem__, default=StringFormat.TEXT, help="format of tier")
  parser.add_argument('--tier-type', choices=IntervalFormat,
                      type=IntervalFormat.__getitem__, default=IntervalFormat.WORD, help="type of tier")
  parser.add_argument("--encoding", type=str, metavar='',
                      help="encoding of text files", default="UTF-8")
  parser.add_argument("--output-directory", metavar='PATH', type=Path,
                      help="directory where to output the text files if not to the same directory")
  add_n_digits_argument(parser)
  add_overwrite_argument(parser)
  return __main


def __main(directory: Path, tier: str, tier_format: StringFormat, tier_type: IntervalFormat, n_digits: int, encoding: str, output_directory: Optional[Path], overwrite: bool) -> ExecutionResult:
  logger = getLogger(__name__)

  if error := DirectoryNotExistsError.validate(directory):
    logger.error(error.default_message)
    return False, False

  if output_directory is None:
    output_directory = directory

  grid_files = get_grid_files(directory)

  total_success = True
  for file_nr, (file_stem, rel_path) in enumerate(grid_files.items(), start=1):
    logger.info(f"Processing {file_stem} ({file_nr}/{len(grid_files)})...")
    text_file_out_abs = output_directory / f"{file_stem}.txt"
    if text_file_out_abs.exists() and not overwrite:
      logger.info("Text file already exists. Skipped.")
      continue

    grid_file_in_abs = directory / rel_path
    grid_in = load_grid(grid_file_in_abs, n_digits)

    (error, _), text = convert_tier_to_text(grid_in, tier, tier_format, tier_type)

    success = error is None
    total_success &= success

    if not success:
      logger.error(error.default_message)
      logger.info("Skipped.")
      continue

    save_text(text_file_out_abs, text, encoding)

  logger.info(f"Written output to: {output_directory}")
  return total_success, False
