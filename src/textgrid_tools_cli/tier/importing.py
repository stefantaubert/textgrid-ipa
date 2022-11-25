from argparse import ArgumentParser, Namespace

from tqdm import tqdm

from textgrid_tools.tier.importing import import_text_to_tier
from textgrid_tools_cli.globals import ExecutionResult
from textgrid_tools_cli.helper import (add_directory_argument, add_encoding_argument,
                                       add_overwrite_argument, add_tier_argument, get_optional,
                                       get_text_files, parse_existing_directory, parse_path,
                                       try_load_grid, try_save_grid)
from textgrid_tools_cli.logging_configuration import get_file_logger, init_and_get_console_logger


def get_importing_parser(parser: ArgumentParser):
  parser.description = "This command imports a tier from a text file."

  add_directory_argument(parser)
  add_tier_argument(parser, "new tier to which the content should be written")
  add_encoding_argument(parser, "encoding of grid and text files")
  parser.add_argument("--text-directory", metavar='TEXT-DIRECTORY', type=get_optional(parse_existing_directory),
                      help="directory where to read the text files; defaults to dictionary if not set", default=None)
  parser.add_argument("-out", "--output-directory", metavar='OUTPUT-DIRECTORY', type=get_optional(parse_path),
                      help="directory where to output the grid files if not to the same directory", default=None)
  parser.add_argument('--sep', type=str, metavar="SYMBOL",
                      help="use this symbol to separate the marks of each interval", default="\n")
  add_overwrite_argument(parser)
  return import_text_to_tier_ns


def import_text_to_tier_ns(ns: Namespace) -> ExecutionResult:
  logger = init_and_get_console_logger(__name__)
  flogger = get_file_logger()

  output_directory = ns.output_directory
  if output_directory is None:
    output_directory = ns.directory

  text_dir = ns.directory
  if ns.text_directory is not None:
    text_dir = ns.text_directory

  text_files = get_text_files(text_dir)

  total_success = True
  for file_nr, (file_stem, rel_path) in enumerate(tqdm(text_files.items()), start=1):
    flogger.info(f"Processing {file_stem}")
    grid_file_in_abs = ns.directory / f"{file_stem}.TextGrid"

    if not grid_file_in_abs.is_file():
      flogger.warning("No corresponding grid found. Skipped.")
      continue

    grid_file_out_abs = output_directory / f"{file_stem}.TextGrid"
    if grid_file_out_abs.exists() and not ns.overwrite:
      flogger.info("Grid already exists. Skipped.")
      continue

    error, grid = try_load_grid(grid_file_in_abs, ns.encoding)

    if error:
      flogger.debug(error.exception)
      flogger.error(error.default_message)
      flogger.info("Skipped.")
      continue
    assert grid is not None

    try:
      text = (text_dir / rel_path).read_text(ns.encoding)
    except Exception as ex:
      flogger.error("Text couldn't be loaded. Skipped")
      flogger.exception(ex)
      continue

    error, _ = import_text_to_tier(grid, ns.tier, text, ns.sep, flogger)

    success = error is None
    total_success &= success

    if not success:
      flogger.error(error.default_message)
      flogger.info("Skipped.")
      continue

    error = try_save_grid(grid_file_out_abs, grid, ns.encoding)
    if error is not None:
      flogger.debug(error.exception)
      flogger.error(error.default_message)
      flogger.info("Skipped.")
      total_success = False
      continue

  logger.info(f"Written output to: {output_directory.absolute()}")
  return total_success, True
