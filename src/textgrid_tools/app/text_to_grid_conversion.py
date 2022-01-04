from argparse import ArgumentParser
from logging import getLogger
from pathlib import Path
from typing import Iterable, Optional, cast

from textgrid_tools.app.helper import (add_n_digits_argument,
                                       add_overwrite_argument, get_audio_files,
                                       get_files_dict, get_text_files,
                                       read_audio, save_grid)
from text_utils import StringFormat
from textgrid_tools.core.mfa.text_to_grid_conversion import (
    can_convert_texts_to_grid, can_parse_meta_content, convert_text_to_grid,
    parse_meta_content)
from tqdm import tqdm

DEFAULT_CHARACTERS_PER_SECOND = 15
META_FILE_TYPE = ".meta"


def init_files_convert_text_to_grid_parser(parser: ArgumentParser):
  parser.description = f"This command converts text files (.txt) into grid files. You can provide an audio directory to set the grid's endTime to the durations of the audio files. Furthermore you can provide meta files ({META_FILE_TYPE}) to define start and end of an audio file."
  parser.add_argument("input_directory", type=Path, metavar="input-directory",
                      help="the directory containing text files, which should be converted to grids")
  parser.add_argument("--audio-directory", type=Path, metavar='',
                      help="the directory containing audio files")
  parser.add_argument("--meta-directory", type=Path, metavar='',
                      help="the directory containing meta files")
  parser.add_argument("--grid-name", type=str, metavar='',
                      help="the name of the generated grid")
  parser.add_argument("--tier", type=str, metavar='',
                      help="the name of the tier containing the text content", default="transcript")
  parser.add_argument("--speech-rate", type=float, default=DEFAULT_CHARACTERS_PER_SECOND, metavar='',
                      help="the speech rate (characters per second) which should be used to calculate the duration of the grids if no corresponding audio file exists")
  parser.add_argument('--text-format', choices=StringFormat, type=StringFormat.__getitem__, default=StringFormat.TEXT,
                      help="the format of the text; use TEXT for normal text and SYMBOLS for symbols separated by space")
  add_n_digits_argument(parser)
  parser.add_argument("--output-directory", type=Path, metavar='',
                      help="the directory where to output the generated grid files if not to input-directory")
  add_overwrite_argument(parser)
  return files_convert_text_to_grid


def files_convert_text_to_grid(input_directory: Path, audio_directory: Optional[Path], meta_directory: Optional[Path], grid_name: Optional[str], tier: str, speech_rate: float, text_format: StringFormat, n_digits: int, output_directory: Optional[Path], overwrite: bool) -> None:
  logger = getLogger(__name__)

  if not input_directory.exists():
    logger.error("Input directory does not exist!")
    return

  if audio_directory is not None and not audio_directory.exists():
    logger.error("Audio directory does not exist!")
    return

  if meta_directory is not None and not meta_directory.exists():
    logger.error("Meta directory does not exist!")
    return

  can_converted = can_convert_texts_to_grid(tier, speech_rate)
  if not can_converted:
    return

  if output_directory is None:
    output_directory = input_directory

  text_files = get_text_files(input_directory)
  logger.info(f"Found {len(text_files)} text files.")
  # print(text_files)

  audio_files = {}
  if audio_directory is not None:
    audio_files = get_audio_files(audio_directory)
    logger.info(f"Found {len(audio_files)} audio files.")
    # print(audio_files)

  meta_files = {}
  if meta_directory is not None:
    meta_files = get_files_dict(meta_directory, filetypes={META_FILE_TYPE})
    logger.info(f"Found {len(meta_files)} meta files.")
    # print(meta_files)

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

    grid_file_out_abs = output_directory / f"{file_stem}.TextGrid"

    if grid_file_out_abs.exists() and not overwrite:
      logger.info("Grid file already exists.")
      logger.info("Skipped.")
      continue

    text_file_in_abs = input_directory / text_files[file_stem]
    text = text_file_in_abs.read_text(encoding="UTF-8")

    audio_in = None
    sample_rate = None
    start = None
    end = None

    if file_stem in audio_files:
      audio_file_in_abs = audio_directory / audio_files[file_stem]
      sample_rate, audio_in = read_audio(audio_file_in_abs)

    if file_stem in meta_files:
      meta_file_in_abs = meta_directory / meta_files[file_stem]
      meta_content = meta_file_in_abs.read_text(encoding="UTF-8")
      can_parse_meta = can_parse_meta_content(meta_content)
      if not can_parse_meta:
        logger.info("Meta file couldn't be parsed!")
      else:
        start, end = parse_meta_content(meta_content)
        logger.info(f"Parsed meta file content: [{start}, {end}].")

    grid_out = convert_text_to_grid(text, audio_in, sample_rate, grid_name, tier,
                                    speech_rate, n_digits, start, end, text_format)

    logger.info("Saving...")
    save_grid(grid_file_out_abs, grid_out)

  logger.info(f"Done. Written output to: {output_directory}")
