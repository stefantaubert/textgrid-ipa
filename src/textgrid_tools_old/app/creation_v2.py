from argparse import ArgumentParser, Namespace
from functools import partial
from logging import getLogger
from multiprocessing.pool import Pool
from time import perf_counter
from typing import Any, Dict, Optional, Tuple

from ordered_set import OrderedSet
from textgrid import TextGrid
from tqdm import tqdm

from textgrid_tools import create_grid_from_text
from textgrid_tools_cli.globals import ExecutionResult
from textgrid_tools_cli.helper import (add_chunksize_argument, add_directory_argument,
                                       add_encoding_argument, add_maxtaskperchild_argument,
                                       add_n_jobs_argument, add_output_directory_argument,
                                       get_audio_files, get_chunks, get_files_dict, get_optional,
                                       get_text_files, parse_existing_directory,
                                       parse_non_empty_or_whitespace, parse_positive_float,
                                       parse_positive_integer)
from textgrid_tools_cli.logging_configuration import (get_file_logger, init_and_get_console_logger,
                                                      init_file_stem_loggers, try_init_file_logger,
                                                      write_file_stem_loggers_to_file_logger)
from textgrid_tools_old.app.io import (load_audio_durations, load_texts, remove_none_from_dict,
                                       save_texts, serialize_grids_v2)

DEFAULT_CHARACTERS_PER_SECOND = 15
META_FILE_TYPE = ".meta"


def xtqdm(x, desc=None, total=None, unit=None):
  yield from x


def get_creation_v2_parser(parser: ArgumentParser):
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
  add_encoding_argument(parser, "encoding of grid, text and meta files")
  parser.add_argument("--chunk", type=parse_positive_integer,
                      help="amount of files to process at a time; defaults to all items if not defined", default=None)
  parser.add_argument("--speech-rate", type=parse_positive_float, default=DEFAULT_CHARACTERS_PER_SECOND, metavar='SPEED',
                      help="the speech rate (characters per second) which should be used to calculate the duration of the grids if no corresponding audio file exists")
  add_output_directory_argument(parser)
  # add_overwrite_argument(parser)
  add_n_jobs_argument(parser)
  add_chunksize_argument(parser)
  add_maxtaskperchild_argument(parser)
  # add_log_argument(parser)
  return app_create_grid_from_text


def process_create_grid(stem: str, name: Optional[str], tier: str, speech_rate: float) -> Tuple[str, Optional[TextGrid]]:
  print(f"start {stem}")
  global process_data_dict
  text, meta, audio = process_data_dict[stem]
  sample_rate = None
  audio_samples_in = None
  if audio is not None:
    sample_rate, audio_samples_in = audio
  logger = getLogger(stem)
  (error, _), grid = create_grid_from_text(text, meta, audio_samples_in,
                                           sample_rate, name, tier, speech_rate, logger)

  success = error is None
  logger.info("finished")

  print(f"processed {stem}")
  if success:
    return stem, grid

  logger.error(error.default_message)
  logger.info("Skipped.")
  return stem, None


def app_create_grid_from_text(ns: Namespace) -> ExecutionResult:
  start = perf_counter()
  if ns.log:
    try_init_file_logger(ns.log)
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
  logger.info(f"Found {len(text_files)} text files.")

  audio_files = {}
  if audio_directory is not None:
    audio_files = get_audio_files(audio_directory)
    logger.info(f"Found {len(audio_files)} audio files.")

  meta_files = {}
  if meta_directory is not None:
    meta_files = get_files_dict(meta_directory, filetypes={META_FILE_TYPE})
    logger.info(f"Found {len(meta_files)} meta files.")

  file_stems = OrderedSet(text_files.keys())

  logging_queues = init_file_stem_loggers(file_stems)

  chunked_list = get_chunks(file_stems, ns.chunk)
  chunked_list = chunked_list[:1]
  total_success = True

  single_core = False

  create_grids_proxy = partial(
    process_create_grid,
    name=ns.name,
    tier=ns.tier,
    speech_rate=ns.speech_rate,
  )

  file_chunk: OrderedSet[str]
  for file_chunk in tqdm(chunked_list, desc="Processing chunks", unit="chunk(s)", position=0):
    # reading texts
    process_data = (
      (stem, ns.directory / text_files[stem])
      for stem in file_chunk
    )
    parsed_text_files = load_texts(process_data, ns.encoding, len(file_chunk))

    # reading audio durations
    relevant_audio_files = set(parsed_text_files.keys()).intersection(audio_files.keys())
    process_data = (
      (stem, audio_directory / audio_files[stem])
      for stem in relevant_audio_files
    )
    parsed_audio_files = load_audio_durations(process_data, len(relevant_audio_files))

    # reading meta files
    relevant_meta_files = set(parsed_text_files.keys()).intersection(meta_files.keys())
    process_data = (
      (stem, meta_directory / meta_files[stem])
      for stem in relevant_meta_files
    )
    parsed_meta_files = load_texts(process_data, ns.encoding, len(
      relevant_meta_files), desc="meta")

    process_data = {
      file_stem: (
        text,
        parsed_meta_files.get(file_stem, None),
        parsed_audio_files.get(file_stem, None)
      )
      for file_stem, text in parsed_text_files.items()
    }

    if single_core:
      created_grids = dict(
        create_grids_proxy(x)
        for x in tqdm(process_data.keys(), total=len(process_data), desc="Processing", unit="file(s)")
      )
    else:
      keys = process_data.keys()
      with Pool(
        processes=ns.n_jobs,
        maxtasksperchild=ns.maxtasksperchild,
        initializer=__init_pool,
        initargs=(process_data,),
      ) as pool:
        iterator = pool.imap_unordered(create_grids_proxy, keys, ns.chunksize)
        iterator = tqdm(iterator, total=len(keys),
                        desc="Processing", unit="file(s)")
        created_grids = dict(iterator)

    remove_none_from_dict(created_grids)

    # saving grids
    serialized_grids = serialize_grids_v2(
      created_grids, ns.n_jobs, ns.chunksize, ns.maxtasksperchild)
    process_data = (
      (stem, output_directory / f"{stem}.TextGrid", text)
      for stem, text in serialized_grids.items()
    )
    successes = save_texts(process_data, ns.encoding, len(serialized_grids))
    total_success &= all(successes)

  write_file_stem_loggers_to_file_logger(logging_queues)

  duration = perf_counter() - start
  flogger.debug(f"Total duration (s): {duration}")
  if ns.log:
    logger = getLogger()
    logger.info(f"Written log to: {ns.log.absolute()}")
  return total_success, True


process_data_dict: Dict[str, Any] = None


def __init_pool(process_data: Dict[str, Any]) -> None:
  global process_data_dict
  process_data_dict = process_data
