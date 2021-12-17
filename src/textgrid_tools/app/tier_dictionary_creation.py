from argparse import ArgumentParser
from logging import getLogger
from pathlib import Path
from typing import Iterable, List, Optional, cast

from general_utils import save_obj
from pronunciation_dict_parser.default_parser import PublicDictType
from pronunciation_dict_parser.export import export
from textgrid.textgrid import TextGrid
from textgrid_tools.app.globals import DEFAULT_N_DIGITS
from textgrid_tools.app.helper import get_grid_files, load_grid
from textgrid_tools.core.mfa.tiers_dictionary_creation import (
    can_get_arpa_pronunciation_dicts_from_texts,
    get_arpa_pronunciation_dicts_from_texts)
from tqdm import tqdm


def init_convert_texts_to_dicts_parser(parser: ArgumentParser):
  arpa_dicts = [
    PublicDictType.MFA_ARPA,
    PublicDictType.CMU_ARPA,
    PublicDictType.LIBRISPEECH_ARPA,
    PublicDictType.PROSODYLAB_ARPA,
  ]
  parser.add_argument("--grid_folder_in", type=Path, required=True)
  parser.add_argument("--tier", type=str, required=True)
  parser.add_argument("--trim_symbols", type=str, nargs='+', required=True)
  parser.add_argument("--n_digits", type=int, default=DEFAULT_N_DIGITS)
  parser.add_argument("--consider_annotations", action="store_true")
  parser.add_argument("--out_path_mfa_dict", type=Path, required=False)
  parser.add_argument("--out_path_punctuation_dict", type=Path, required=False)
  parser.add_argument("--out_path_cache", type=Path, required=False)
  parser.add_argument("--dict_type", choices=arpa_dicts,
                      type=PublicDictType.__getitem__, required=True)
  parser.add_argument("--overwrite", action="store_true")
  return convert_texts_to_arpa_dicts


def convert_texts_to_arpa_dicts(grid_folder_in: Path, tier: str, trim_symbols: List[str], consider_annotations: bool, n_jobs: int, out_path_mfa_dict: Optional[Path], out_path_cache: Optional[Path], out_path_punctuation_dict: Optional[Path], dict_type: PublicDictType, n_digits: int, overwrite: bool) -> None:
  logger = getLogger(__name__)

  if not grid_folder_in.exists():
    logger.error("Textgrid folder does not exist!")
    return

  if out_path_mfa_dict is not None and out_path_mfa_dict.is_file() and not overwrite:
    logger.error(f"{out_path_mfa_dict} already exists!")
    return

  if out_path_punctuation_dict is not None and out_path_punctuation_dict.is_file() and not overwrite:
    logger.error(f"{out_path_punctuation_dict} already exists!")
    return

  trim_symbols_set = set(trim_symbols)
  logger.info(f"Trim symbols: {' '.join(sorted(trim_symbols_set))} (#{len(trim_symbols_set)})")

  grid_files = get_grid_files(grid_folder_in)
  logger.info(f"Found {len(grid_files)} grid files.")

  logger.info("Reading files...")
  grids: List[TextGrid] = []
  for file_stem in cast(Iterable[str], tqdm(grid_files)):
    logger.info(f"Processing {file_stem} ...")

    grid_file_in_abs = grid_folder_in / grid_files[file_stem]
    grid_in = load_grid(grid_file_in_abs, n_digits)
    grids.append(grid_in)

  can_remove = can_get_arpa_pronunciation_dicts_from_texts(grids, tier)
  if not can_remove:
    return

  logger.info("Producing dictionary...")
  pronunciation_dict, pronunciation_dict_punctuation, cache = get_arpa_pronunciation_dicts_from_texts(
    grids=grids,
    tier=tier,
    trim_symbols=trim_symbols_set,
    dict_type=dict_type,
    consider_annotations=consider_annotations,
    ignore_case=True,
    n_jobs=n_jobs,
    split_on_hyphen=True,
  )

  if out_path_mfa_dict is not None:
    logger.info(f"Saving {out_path_mfa_dict} ...")
    export(
      include_counter=True,
      path=out_path_mfa_dict,
      pronunciation_dict=pronunciation_dict,
      symbol_sep=" ",
      word_pronunciation_sep="  ",
    )
    logger.info(f"Written pronunciation dictionary for MFA alignment to: {out_path_mfa_dict}")

  if out_path_punctuation_dict is not None:
    logger.info(f"Saving {out_path_punctuation_dict} ...")
    export(
      include_counter=True,
      path=out_path_punctuation_dict,
      pronunciation_dict=pronunciation_dict_punctuation,
      symbol_sep=" ",
      word_pronunciation_sep="  ",
    )
    logger.info(
        f"Written pronunciation dictionary for adding punctuation phonemes to: {out_path_punctuation_dict}")

  if out_path_cache is not None:
    logger.info(f"Saving {out_path_cache} ...")
    save_obj(cache, out_path_cache)
    logger.info(
        f"Written cache to: {out_path_cache}")

  return