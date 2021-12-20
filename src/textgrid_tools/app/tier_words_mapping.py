from argparse import ArgumentParser
from logging import getLogger
from pathlib import Path
from typing import Iterable, cast

from pronunciation_dict_parser.parser import parse_file
from textgrid_tools.app.globals import DEFAULT_N_DIGITS
from textgrid_tools.app.helper import get_grid_files, load_grid, save_grid
from textgrid_tools.core.mfa.tier_words_mapping import (can_map_words_to_tier,
                                                        map_words_to_tier)
from tqdm import tqdm


def init_files_map_words_to_tier_parser(parser: ArgumentParser):
  parser.add_argument("--grid_folder_in", type=Path, required=True)
  parser.add_argument("--tier", type=str, required=True)
  parser.add_argument("--reference_grid_folder_in", type=Path, required=True)
  parser.add_argument("--reference_tier", type=str, required=True)
  parser.add_argument("--path_align_dict", type=Path, required=True)
  parser.add_argument("--new_tier", type=str, required=True)
  parser.add_argument("--n_digits", type=int, default=DEFAULT_N_DIGITS)
  parser.add_argument("--grid_folder_out", type=Path, required=True)
  parser.add_argument("--overwrite_tier", action="store_true")
  parser.add_argument("--overwrite", action="store_true")
  return files_map_words_to_tier


def files_map_words_to_tier(grid_folder_in: Path, tier: str, reference_grid_folder_in: Path, reference_tier: str, path_align_dict: Path, new_tier: str, n_digits: int, grid_folder_out: Path, overwrite_tier: bool, overwrite: bool) -> None:
  logger = getLogger(__name__)

  if not grid_folder_in.exists():
    logger.error("Textgrid folder does not exist!")
    return

  if not reference_grid_folder_in.exists():
    logger.error("Reference textgrid folder does not exist!")
    return

  if not path_align_dict.exists():
    logger.error("Alignment dictionary does not exist!")
    return

  grid_files = get_grid_files(grid_folder_in)
  logger.info(f"Found {len(grid_files)} grid files.")

  ref_grid_files = get_grid_files(reference_grid_folder_in)
  logger.info(f"Found {len(ref_grid_files)} reference grid files.")

  common_files = set(grid_files.keys()).intersection(ref_grid_files.keys())
  missing_grid_files = set(ref_grid_files.keys()).difference(grid_files.keys())
  missing_ref_grid_files = set(grid_files.keys()).difference(ref_grid_files.keys())

  logger.info(f"{len(missing_grid_files)} grid files missing.")
  logger.info(f"{len(missing_ref_grid_files)} reference grid files missing.")

  logger.info(f"Found {len(common_files)} matching files.")

  alignment_dict = parse_file(path_align_dict)

  logger.info("Reading files...")
  for file_stem in cast(Iterable[str], tqdm(common_files)):
    logger.info(f"Processing {file_stem} ...")

    grid_file_out_abs = grid_folder_out / grid_files[file_stem]

    if grid_file_out_abs.exists() and not overwrite:
      logger.info("Target grids already exists.")
      logger.info("Skipped.")
      continue

    grid_file_in_abs = grid_folder_in / grid_files[file_stem]
    grid_in = load_grid(grid_file_in_abs, n_digits)

  logger.info("Reading files...")
  for file_stem in cast(Iterable[str], tqdm(grid_files)):
    logger.info(f"Processing {file_stem} ...")

    grid_file_out_abs = grid_folder_out / grid_files[file_stem]

    if grid_file_out_abs.exists() and not overwrite:
      logger.info("Target grid already exists.")
      logger.info("Skipped.")
      continue

    grid_file_in_abs = grid_folder_in / grid_files[file_stem]
    grid_in = load_grid(grid_file_in_abs, n_digits)

    ref_grid_file_in_abs = reference_grid_folder_in / ref_grid_files[file_stem]
    ref_grid_in = load_grid(ref_grid_file_in_abs, n_digits)

    can_map = can_map_words_to_tier(
      grid_in, tier, ref_grid_in, reference_tier, alignment_dict, new_tier, overwrite_tier)
    if not can_map:
      logger.info("Skipped.")
      continue
    try:
      map_words_to_tier(grid_in, tier, ref_grid_in, reference_tier,
                        alignment_dict, new_tier, overwrite_tier)
    except Exception as ex:
      logger.info("Skipped.")
      continue

    logger.info("Saving...")
    save_grid(grid_file_out_abs, grid_in)

  logger.info(f"Done. Written output to: {grid_folder_out}")
