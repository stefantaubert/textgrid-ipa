from argparse import ArgumentParser
from logging import getLogger
from pathlib import Path
from typing import Iterable, cast

from textgrid_tools.app.globals import DEFAULT_N_DIGITS
from textgrid_tools.app.helper import get_grid_files, load_grid
from textgrid_tools.core.mfa.grid_to_text_conversion import (
    can_convert_tier_to_text, convert_tier_to_text)
from textgrid_tools.core.mfa.string_format import StringFormat
from tqdm import tqdm


def init_files_convert_grid_to_text_parser(parser: ArgumentParser):
  parser.description = "This command writes the content of a tier into a text file."
  parser.add_argument("--grid_folder_in", type=Path, required=True)
  parser.add_argument("--tier", type=str, required=True)
  parser.add_argument('--string_format', choices=StringFormat,
                      type=StringFormat.__getitem__, default=StringFormat.TEXT)
  parser.add_argument("--n_digits", type=int, default=DEFAULT_N_DIGITS)
  parser.add_argument("--text_folder_out", type=Path, required=True)
  parser.add_argument("--overwrite", action="store_true")
  return files_convert_grid_to_text


def files_convert_grid_to_text(grid_folder_in: Path, tier: str, string_format: StringFormat, n_digits: int, text_folder_out: Path, overwrite: bool) -> None:
  logger = getLogger(__name__)

  if not grid_folder_in.exists():
    logger.error("Textgrid folder does not exist!")
    return

  grid_files = get_grid_files(grid_folder_in)
  logger.info(f"Found {len(grid_files)} grid files.")

  logger.info("Reading files...")
  for file_stem in cast(Iterable[str], tqdm(grid_files)):
    logger.info(f"Processing {file_stem} ...")

    text_file_out_abs = text_folder_out / f"{file_stem}.txt"

    if text_file_out_abs.exists() and not overwrite:
      logger.info("Target text already exists.")
      logger.info("Skipped.")
      continue

    grid_file_in_abs = grid_folder_in / grid_files[file_stem]
    grid_in = load_grid(grid_file_in_abs, n_digits)

    can_remove = can_convert_tier_to_text(grid_in, tier)
    if not can_remove:
      logger.info("Skipped.")
      continue

    text = convert_tier_to_text(grid_in, tier, string_format)

    logger.info("Saving...")
    text_file_out_abs.parent.mkdir(parents=True, exist_ok=True)
    text_file_out_abs.write_text(text, encoding="UTF-8")

  logger.info(f"Done. Written output to: {text_folder_out}")
