from argparse import ArgumentParser
from logging import getLogger
from pathlib import Path
from typing import Optional

from textgrid_tools.tier.importing import import_text_to_tier
from textgrid_tools_cli.globals import ExecutionResult
from textgrid_tools_cli.helper import (add_directory_argument, add_encoding_argument,
                                       add_n_digits_argument, add_overwrite_argument,
                                       add_tier_argument, get_grid_files, get_optional,
                                       get_text_files, parse_existing_directory, parse_path,
                                       save_grid, try_load_grid)


def get_importing_parser(parser: ArgumentParser):
  parser.description = "This command imports a tier from a text file."

  add_directory_argument(parser)
  add_tier_argument(parser, "new tier to which the content should be written")
  add_encoding_argument(parser, "encoding of text files")
  parser.add_argument("--text-directory", metavar='PATH', type=get_optional(parse_existing_directory),
                      help="directory where to read the text files; defaults to dictionary if not set", default=None)
  parser.add_argument("-out", "--output-directory", metavar='PATH', type=get_optional(parse_path),
                      help="directory where to output the grid files if not to the same directory", default=None)
  parser.add_argument('--sep', type=str, metavar="SYMBOL",
                      help="use this symbol to separate the marks of each interval", default="\n")
  add_n_digits_argument(parser)
  add_overwrite_argument(parser)
  return import_text_to_tier_ns


def import_text_to_tier_ns(directory: Path, tier: str, sep: str, text_directory: Optional[Path], n_digits: int, encoding: str, output_directory: Optional[Path], overwrite: bool) -> ExecutionResult:
  logger = getLogger(__name__)

  if output_directory is None:
    output_directory = directory

  grid_files = get_grid_files(directory)
  text_dir = directory
  if text_directory is not None:
    text_dir = text_directory

  text_files = get_text_files(text_dir)

  total_success = True
  for file_nr, (file_stem, rel_path) in enumerate(text_files.items(), start=1):
    logger.info(f"Processing {file_stem} ({file_nr}/{len(grid_files)})...")
    grid_file_in_abs = directory / f"{file_stem}.TextGrid"

    if not grid_file_in_abs.is_file():
      logger.warning("No corresponding grid found. Skipped.")
      continue

    grid_file_out_abs = output_directory / f"{file_stem}.TextGrid"
    if grid_file_out_abs.exists() and not overwrite:
      logger.info("Grid already exists. Skipped.")
      continue

    error, grid = try_load_grid(grid_file_in_abs, n_digits)

    if error:
      logger.error(error.default_message)
      logger.info("Skipped.")
      continue
    assert grid is not None

    try:
      text = (text_dir / rel_path).read_text(encoding)
    except Exception as ex:
      logger.error("Text couldn't be loaded. Skipped")
      logger.exception(ex)
      continue

    error, _ = import_text_to_tier(grid, tier, text, sep)

    success = error is None
    total_success &= success

    if not success:
      logger.error(error.default_message)
      logger.info("Skipped.")
      continue

    save_grid(grid_file_out_abs, grid)

  logger.info(f"Written output to: {output_directory.absolute()}")
  return total_success, True
