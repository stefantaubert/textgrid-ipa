from argparse import ArgumentParser
from logging import getLogger
from pathlib import Path
from typing import Iterable, Optional, cast

from textgrid_tools.app.helper import get_text_files, save_grid
from textgrid_tools.core.mfa.text_to_grid_conversion import (
    can_convert_text_to_grid, convert_text_to_grid)
from textgrid_tools.core.mfa.string_format import StringFormat
from tqdm import tqdm

DEFAULT_CHARACTERS_PER_SECOND = 15


def init_files_convert_text_to_grid_parser(parser: ArgumentParser):
  parser.add_argument("--text_folder_in", type=Path, required=True)
  parser.add_argument("--grid_name_out", type=str, required=False)
  parser.add_argument("--tier_out", type=str, required=True)
  parser.add_argument("--characters_per_second", type=float, default=DEFAULT_CHARACTERS_PER_SECOND)
  parser.add_argument('--string_format', choices=StringFormat,
                      type=StringFormat.__getitem__, default=StringFormat.TEXT)
  parser.add_argument("--grid_folder_out", type=Path, required=True)
  parser.add_argument("--overwrite", action="store_true")
  return files_convert_text_to_grid


def files_convert_text_to_grid(text_folder_in: Path, grid_name_out: Optional[str], tier_out: str, characters_per_second: float, string_format: StringFormat, grid_folder_out: Path, overwrite: bool) -> None:
  logger = getLogger(__name__)

  if not text_folder_in.exists():
    logger.error("Text folder does not exist!")
    return

  can_converted = can_convert_text_to_grid(tier_out, characters_per_second)
  if not can_converted:
    return

  text_files = get_text_files(text_folder_in)
  logger.info(f"Found {len(text_files)} text files.")

  logger.info("Reading files...")
  for file_stem in cast(Iterable[str], tqdm(text_files)):
    logger.info(f"Processing {file_stem} ...")

    grid_file_out_abs = grid_folder_out / file_stem + ".TextGrid"

    if grid_file_out_abs.exists() and not overwrite:
      logger.info("Target grid already exists.")
      logger.info("Skipped.")
      continue

    text_file_in_abs = text_folder_in / text_files[file_stem]
    text = text_file_in_abs.read_text()

    grid_out = convert_text_to_grid(text, grid_name_out, tier_out,
                                    characters_per_second, string_format)

    logger.info("Saving...")
    save_grid(grid_file_out_abs, grid_out)

  logger.info(f"Done. Written output to: {grid_folder_out}")
