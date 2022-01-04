from argparse import ArgumentParser
from logging import getLogger
from pathlib import Path
from typing import Iterable, Optional, cast

from text_utils import StringFormat
from textgrid_tools.app.globals import DEFAULT_N_DIGITS
from textgrid_tools.app.helper import (add_n_digits_argument,
                                       add_overwrite_argument, get_grid_files,
                                       load_grid)
from textgrid_tools.core.mfa.grid_to_text_conversion import (
    can_convert_tier_to_text, convert_tier_to_text)
from tqdm import tqdm


def init_files_convert_grid_to_text_parser(parser: ArgumentParser):
  parser.description = "This command writes the content of a tier into a text file."

  parser.add_argument("directory", type=Path, metavar="directory",
                      help="the directory containing grid files, from which intervals should be removed")
  parser.add_argument("tier", type=str, help="the tier on which intervals should be removed")
  parser.add_argument('--string-format', choices=StringFormat,
                      type=StringFormat.__getitem__, default=StringFormat.TEXT)
  parser.add_argument("--output-directory", type=Path, default=None,
                      help="custom directory where to write the text files if not to directory")
  add_n_digits_argument(parser)
  add_overwrite_argument(parser)
  return files_convert_grid_to_text


def files_convert_grid_to_text(directory: Path, tier: str, string_format: StringFormat, n_digits: int, output_directory: Optional[Path], overwrite: bool) -> None:
  logger = getLogger(__name__)

  if not directory.exists():
    logger.error("Textgrid folder does not exist!")
    return

  if output_directory is None:
    output_directory = directory

  grid_files = get_grid_files(directory)
  logger.info(f"Found {len(grid_files)} grid files.")

  logger.info("Reading files...")
  for file_stem in cast(Iterable[str], tqdm(grid_files)):
    logger.info(f"Processing {file_stem} ...")

    text_file_out_abs = output_directory / f"{file_stem}.txt"

    if text_file_out_abs.exists() and not overwrite:
      logger.info("Target text already exists.")
      logger.info("Skipped.")
      continue

    grid_file_in_abs = directory / grid_files[file_stem]
    grid_in = load_grid(grid_file_in_abs, n_digits)

    can_remove = can_convert_tier_to_text(grid_in, tier)
    if not can_remove:
      logger.info("Skipped.")
      continue

    text = convert_tier_to_text(grid_in, tier, string_format)

    logger.info("Saving...")
    text_file_out_abs.parent.mkdir(parents=True, exist_ok=True)
    text_file_out_abs.write_text(text, encoding="UTF-8")

  logger.info(f"Done. Written output to: {output_directory}")
