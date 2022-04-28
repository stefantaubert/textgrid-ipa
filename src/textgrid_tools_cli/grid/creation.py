from argparse import ArgumentParser
from logging import getLogger
from pathlib import Path
from typing import Optional

from text_utils import StringFormat
from textgrid_tools_cli.globals import ExecutionResult
from textgrid_tools_cli.helper import (add_directory_argument,
                                       add_encoding_argument,
                                       add_n_digits_argument,
                                       add_output_directory_argument,
                                       add_overwrite_argument,
                                       add_string_format_argument,
                                       get_audio_files, get_files_dict,
                                       get_optional, get_text_files,
                                       parse_existing_directory,
                                       parse_non_empty_or_whitespace,
                                       parse_positive_float, read_audio,
                                       save_grid)
from textgrid_tools import create_grid_from_text

DEFAULT_CHARACTERS_PER_SECOND = 15
META_FILE_TYPE = ".meta"


def get_creation_parser(parser: ArgumentParser):
  parser.description = f"This command converts text files (.txt) into grid files. You can provide an audio directory to set the grid's endTime to the durations of the audio files. Furthermore you can provide meta files ({META_FILE_TYPE}) to define start and end of an audio file."
  add_directory_argument(parser, "directory containing text, audio and meta files")
  parser.add_argument("--tier", type=parse_non_empty_or_whitespace, metavar='NAME',
                      help="the name of the tier containing the text content", default="transcript")
  parser.add_argument("--audio-directory", type=get_optional(parse_existing_directory), metavar='PATH',
                      help="directory containing audio files if not directory")
  parser.add_argument("--meta-directory", type=get_optional(parse_existing_directory), metavar='PATH',
                      help="directory containing meta files; defaults to directory if not specified", default=None)
  parser.add_argument("--name", type=str, metavar='NAME',
                      help="name of the grid")
  add_encoding_argument(parser, "encoding of text and meta files")
  parser.add_argument("--speech-rate", type=parse_positive_float, default=DEFAULT_CHARACTERS_PER_SECOND, metavar='SPEED',
                      help="the speech rate (characters per second) which should be used to calculate the duration of the grids if no corresponding audio file exists")
  add_string_format_argument(parser, "text files")
  add_n_digits_argument(parser)
  add_output_directory_argument(parser)
  add_overwrite_argument(parser)
  return app_create_grid_from_text


def app_create_grid_from_text(directory: Path, audio_directory: Optional[Path], meta_directory: Optional[Path], name: Optional[str], tier: str, speech_rate: float, formatting: StringFormat, n_digits: int, output_directory: Optional[Path], encoding: str, overwrite: bool) -> ExecutionResult:
  logger = getLogger(__name__)

  if audio_directory is None:
    audio_directory = directory

  if meta_directory is None:
    meta_directory = directory

  if output_directory is None:
    output_directory = directory

  text_files = get_text_files(directory)

  audio_files = {}
  if audio_directory is not None:
    audio_files = get_audio_files(audio_directory)

  meta_files = {}
  if meta_directory is not None:
    meta_files = get_files_dict(meta_directory, filetypes={META_FILE_TYPE})
    logger.info(f"Found {len(meta_files)} meta files.")

  total_success = True
  for file_nr, (file_stem, rel_path) in enumerate(text_files.items(), start=1):
    logger.info(f"Processing {file_stem} ({file_nr}/{len(text_files)})...")
    grid_file_out_abs = output_directory / f"{file_stem}.TextGrid"
    if grid_file_out_abs.exists() and not overwrite:
      logger.info("Grid already exists. Skipped.")
      continue

    text_file_in_abs = directory / rel_path
    text = text_file_in_abs.read_text(encoding)

    audio_in = None
    sample_rate = None
    meta = None

    if file_stem in audio_files:
      audio_file_in_abs = audio_directory / audio_files[file_stem]
      sample_rate, audio_in = read_audio(audio_file_in_abs)
    else:
      logger.info("No audio found, audio duration will be estimated.")

    if file_stem in meta_files:
      meta_file_in_abs = meta_directory / meta_files[file_stem]
      meta = meta_file_in_abs.read_text(encoding)
    else:
      logger.info("No meta file found.")

    (error, _), grid = create_grid_from_text(text, formatting, meta, audio_in,
                                             sample_rate, name, tier, speech_rate, n_digits)

    success = error is None
    total_success &= success

    if not success:
      logger.error(error.default_message)
      logger.info("Skipped.")
      continue

    save_grid(grid_file_out_abs, grid)

  return total_success, True
