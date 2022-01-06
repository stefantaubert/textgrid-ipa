from argparse import ArgumentParser
from logging import getLogger
from pathlib import Path
from typing import Iterable, cast

from textgrid_tools.app.globals import DEFAULT_N_DIGITS
from textgrid_tools.app.helper import get_grid_files, load_grid, save_grid
from textgrid_tools.core.mfa.tier_arpa_to_ipa_mapping import (
    can_map_arpa_to_ipa, map_arpa_to_ipa)
from tqdm import tqdm


def init_map_arpa_tier_to_ipa_parser(parser: ArgumentParser):
  parser.description = "This command maps ARPA transcriptions to IPA."
  parser.add_argument("--grid_folder_in", type=Path, required=True)
  parser.add_argument("--arpa_tier_in", type=str, required=True)
  parser.add_argument("--ipa_tier_out", type=str, required=True)
  parser.add_argument("--n_digits", type=int, default=DEFAULT_N_DIGITS)
  parser.add_argument("--grid_folder_out", type=Path, required=True)
  parser.add_argument("--overwrite_tier", action="store_true")
  parser.add_argument("--overwrite", action="store_true")
  return map_arpa_tier_to_ipa


def map_arpa_tier_to_ipa(grid_folder_in: Path, arpa_tier_in: str, ipa_tier_out: str, n_digits: int, overwrite_tier: bool, grid_folder_out: Path, overwrite: bool) -> None:
  logger = getLogger(__name__)

  if not grid_folder_in.exists():
    logger.error("Textgrid folder does not exist!")
    return

  grid_files = get_grid_files(grid_folder_in)
  logger.info(f"Found {len(grid_files)} grid files.")

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

    can_map = can_map_arpa_to_ipa(
      grid=grid_in,
      arpa_tier_name=arpa_tier_in,
      ipa_tier_name=ipa_tier_out,
      overwrite_existing_tier=overwrite_tier,
    )

    if not can_map:
      logger.info("Skipped.")
      continue

    map_arpa_to_ipa(
      grid=grid_in,
      tier_name=arpa_tier_in,
      custom_output_tier_name=ipa_tier_out,
      overwrite_tier=overwrite_tier,
    )

    logger.info("Saving...")
    save_grid(grid_file_out_abs, grid_in)

  logger.info(f"Done. Written output to: {grid_folder_out}")
