from argparse import ArgumentParser, Namespace
from logging import getLogger

from textgrid_tools import convert_tier_to_text
from textgrid_tools_cli.globals import ExecutionResult
from textgrid_tools_cli.helper import (add_directory_argument, add_encoding_argument,
                                       add_overwrite_argument, add_tier_argument, get_grid_files,
                                       get_optional, parse_path, save_text, try_load_grid)


def get_exporting_parser(parser: ArgumentParser):
  parser.description = "This command writes the content of a tier into a text file."

  add_directory_argument(parser)
  add_tier_argument(parser, "tier from which the content should be written")
  add_encoding_argument(parser, "encoding of grid and text files")
  parser.add_argument("-out", "--output-directory", metavar='PATH', type=get_optional(parse_path),
                      help="directory where to output the text files if not to the same directory", default=None)
  parser.add_argument('--sep', type=str, metavar="SYMBOL",
                      help="use this symbol to separate the marks of each interval", default="\n")
  add_overwrite_argument(parser)
  return app_convert_tier_to_text


def app_convert_tier_to_text(ns: Namespace) -> ExecutionResult:
  logger = getLogger(__name__)

  output_directory = ns.output_directory
  if output_directory is None:
    output_directory = ns.directory

  grid_files = get_grid_files(ns.directory)

  total_success = True
  for file_nr, (file_stem, rel_path) in enumerate(grid_files.items(), start=1):
    logger.info(f"Processing {file_stem} ({file_nr}/{len(grid_files)})...")
    text_file_out_abs = output_directory / f"{file_stem}.txt"
    if text_file_out_abs.exists() and not ns.overwrite:
      logger.info("Text file already exists. Skipped.")
      continue

    grid_file_in_abs = ns.directory / rel_path
    error, grid = try_load_grid(grid_file_in_abs, ns.encoding)

    if error:
      logger.error(error.default_message)
      logger.info("Skipped.")
      continue
    assert grid is not None

    (error, _), text = convert_tier_to_text(grid, ns.tier, ns.sep)

    success = error is None
    total_success &= success

    if not success:
      logger.error(error.default_message)
      logger.info("Skipped.")
      continue

    save_text(text_file_out_abs, text, ns.encoding)

  logger.info(f"Written output to: {output_directory}")
  return total_success, True
