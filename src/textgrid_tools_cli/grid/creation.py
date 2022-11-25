from argparse import ArgumentParser, Namespace

from tqdm import tqdm

from textgrid_tools import create_grid_from_text
from textgrid_tools_cli.globals import ExecutionResult
from textgrid_tools_cli.helper import (add_directory_argument, add_encoding_argument,
                                       add_output_directory_argument, add_overwrite_argument,
                                       get_audio_files, get_files_dict, get_optional,
                                       get_text_files, parse_existing_directory,
                                       parse_non_empty_or_whitespace, parse_positive_float,
                                       read_audio, try_save_grid)
from textgrid_tools_cli.logging_configuration import get_file_logger, init_and_get_console_logger

DEFAULT_CHARACTERS_PER_SECOND = 15
META_FILE_TYPE = ".meta"


def get_creation_parser(parser: ArgumentParser):
  parser.description = f"This command converts text files (.txt) into grid files. You can provide an audio directory to set the grid's endTime to the durations of the audio files. Furthermore you can provide meta files ({META_FILE_TYPE}) to define start and end of an audio file."
  add_directory_argument(parser, "directory containing text, audio and meta files")
  parser.add_argument("--tier", type=parse_non_empty_or_whitespace, metavar='TIER',
                      help="the name of the tier containing the text content", default="transcript")
  parser.add_argument("--audio-directory", type=get_optional(parse_existing_directory), metavar='AUDIO-PATH',
                      help="directory containing audio files if not directory")
  parser.add_argument("--meta-directory", type=get_optional(parse_existing_directory), metavar='META-PATH',
                      help="directory containing meta files; defaults to directory if not specified", default=None)
  parser.add_argument("--name", type=str, metavar='NAME',
                      help="name of the grid")
  add_encoding_argument(parser, "encoding of grid, text and meta files")
  parser.add_argument("--speech-rate", type=parse_positive_float, default=DEFAULT_CHARACTERS_PER_SECOND, metavar='SPEED',
                      help="the speech rate (characters per second) which should be used to calculate the duration of the grids if no corresponding audio file exists")
  add_output_directory_argument(parser)
  add_overwrite_argument(parser)
  return app_create_grid_from_text


def app_create_grid_from_text(ns: Namespace) -> ExecutionResult:
  logger = init_and_get_console_logger(__name__)
  flogger = get_file_logger()

  audio_directory = ns.audio_directory
  if audio_directory is None:
    audio_directory = ns.directory

  meta_directory = ns.meta_directory
  if meta_directory is None:
    meta_directory = ns.directory

  output_directory = ns.output_directory
  if output_directory is None:
    output_directory = ns.directory

  text_files = get_text_files(ns.directory)

  audio_files = {}
  if audio_directory is not None:
    audio_files = get_audio_files(audio_directory)

  meta_files = {}
  if meta_directory is not None:
    meta_files = get_files_dict(meta_directory, filetypes={META_FILE_TYPE})
    logger.info(f"Found {len(meta_files)} meta file(s).")

  logging_queues = dict.fromkeys(text_files.keys())
  total_success = True
  for file_nr, (file_stem, rel_path) in enumerate(tqdm(text_files.items()), start=1):
    flogger.info(f"Processing {file_stem}")
    grid_file_out_abs = output_directory / f"{file_stem}.TextGrid"
    if grid_file_out_abs.exists() and not ns.overwrite:
      flogger.info("Grid already exists. Skipped.")
      continue

    text_file_in_abs = ns.directory / rel_path
    text = text_file_in_abs.read_text(ns.encoding)

    audio_samples_in = None
    sample_rate = None
    meta = None

    if file_stem in audio_files:
      audio_file_in_abs = audio_directory / audio_files[file_stem]
      try:
        sample_rate, audio_in = read_audio(audio_file_in_abs)
      except Exception as ex:
        flogger.exception(ex)
        flogger.error(f"Audio file '{audio_file_in_abs.absolute()}' could not be read!")
        flogger.info("Skipped.")
        total_success = False
        continue
      audio_samples_in = audio_in.shape[0]
    else:
      flogger.info("No audio found, audio duration will be estimated.")

    if file_stem in meta_files:
      meta_file_in_abs = meta_directory / meta_files[file_stem]
      try:
        meta = meta_file_in_abs.read_text(ns.encoding)
      except Exception as ex:
        flogger.exception(ex)
        flogger.error(f"Meta file '{meta_file_in_abs.absolute()}' could not be read!")
        flogger.info("Skipped.")
        total_success = False
        continue
    else:
      flogger.info("No meta file found.")

    (error, _), grid = create_grid_from_text(text, meta, audio_samples_in,
                                             sample_rate, ns.name, ns.tier, ns.speech_rate, flogger)

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

  return total_success, True
