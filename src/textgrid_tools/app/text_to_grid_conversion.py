from argparse import ArgumentParser
from logging import getLogger
from pathlib import Path
from typing import Iterable, Optional, cast

from scipy.io.wavfile import read
from textgrid_tools.app.globals import DEFAULT_N_DIGITS
from textgrid_tools.app.helper import (get_audio_files, get_files_dict,
                                       get_text_files, save_grid)
from textgrid_tools.core.mfa.string_format import StringFormat
from textgrid_tools.core.mfa.text_to_grid_conversion import (
    can_convert_texts_to_grid, can_parse_meta_content, convert_text_to_grid,
    parse_meta_content)
from tqdm import tqdm

DEFAULT_CHARACTERS_PER_SECOND = 15
META_FILE_TYPE = ".meta"


def init_files_convert_text_to_grid_parser(parser: ArgumentParser):
  parser.add_argument("--text_folder_in", type=Path, required=True)
  parser.add_argument("--audio_folder_in", type=Path, required=False)
  parser.add_argument("--meta_folder_in", type=Path, required=False)
  parser.add_argument("--grid_name_out", type=str, required=False)
  parser.add_argument("--tier_out", type=str, required=True)
  parser.add_argument("--characters_per_second", type=float, default=DEFAULT_CHARACTERS_PER_SECOND)
  parser.add_argument('--string_format', choices=StringFormat,
                      type=StringFormat.__getitem__, default=StringFormat.TEXT)
  parser.add_argument("--n_digits", type=int, default=DEFAULT_N_DIGITS)
  parser.add_argument("--grid_folder_out", type=Path, required=True)
  parser.add_argument("--overwrite", action="store_true")
  return files_convert_text_to_grid


def files_convert_text_to_grid(text_folder_in: Path, audio_folder_in: Optional[Path], meta_folder_in: Optional[Path], grid_name_out: Optional[str], tier_out: str, characters_per_second: float, string_format: StringFormat, n_digits: int, grid_folder_out: Path, overwrite: bool) -> None:
  logger = getLogger(__name__)

  if not text_folder_in.exists():
    logger.error("Text folder does not exist!")
    return

  if audio_folder_in is not None and not audio_folder_in.exists():
    logger.error("Audio folder does not exist!")
    return

  if meta_folder_in is not None and not meta_folder_in.exists():
    logger.error("Meta folder does not exist!")
    return

  can_converted = can_convert_texts_to_grid(tier_out, characters_per_second)
  if not can_converted:
    return

  text_files = get_text_files(text_folder_in)
  logger.info(f"Found {len(text_files)} text files.")

  audio_files = {}
  if audio_folder_in is not None:
    audio_files = get_audio_files(audio_folder_in)
    logger.info(f"Found {len(audio_files)} audio files.")

  meta_files = {}
  if meta_folder_in is not None:
    meta_files = get_files_dict(audio_folder_in, filetypes={META_FILE_TYPE})
    logger.info(f"Found {len(meta_files)} meta files.")

  common_files = set(text_files.keys()).intersection(audio_files.keys())
  missing_grid_files = set(audio_files.keys()).difference(text_files.keys())
  missing_audio_files = set(text_files.keys()).difference(audio_files.keys())

  logger.info(f"{len(missing_grid_files)} text files missing.")
  logger.info(
    f"{len(missing_audio_files)} audio files missing. For these files the audio duration is estimated.")

  logger.info(f"Found {len(common_files)} matching files.")

  logger.info("Reading files ...")
  for file_stem in cast(Iterable[str], tqdm(text_files)):
    logger.info(f"Processing {file_stem} ...")

    grid_file_out_abs = grid_folder_out / f"{file_stem}.TextGrid"

    if grid_file_out_abs.exists() and not overwrite:
      logger.info("Target grid already exists.")
      logger.info("Skipped.")
      continue

    text_file_in_abs = text_folder_in / text_files[file_stem]
    text = text_file_in_abs.read_text()

    audio_in = None
    sample_rate = None
    if file_stem in audio_files:
      audio_file_in_abs = audio_folder_in / audio_files[file_stem]
      sample_rate, audio_in = read(audio_file_in_abs)
    if file_stem in meta_files:
      meta_file_in_abs = meta_folder_in / meta_files[file_stem]
      meta_content = meta_file_in_abs.read_text(encoding="UTF-8")
      can_parse_meta = can_parse_meta_content(meta_content)
      if not can_parse_meta:
        logger.info("Meta couldn't be parsed!")
        start = None
        end = None
      else:
        start, end = parse_meta_content(meta_content)
        logger.info(f"Parsed meta [{start}, {end}].")

    grid_out = convert_text_to_grid(text, audio_in, sample_rate, grid_name_out, tier_out,
                                    characters_per_second, n_digits, start, end, string_format)

    logger.info("Saving...")
    save_grid(grid_file_out_abs, grid_out)

  logger.info(f"Done. Written output to: {grid_folder_out}")
