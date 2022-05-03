import multiprocessing
import threading
from argparse import ArgumentParser
from functools import partial
from logging import getLogger
from multiprocessing.pool import ThreadPool
from pathlib import Path
from typing import List, Optional, Tuple

from ordered_set import OrderedSet
from textgrid import TextGrid
from tqdm import tqdm

from textgrid_tools import create_grid_from_text
from textgrid_tools_cli.globals import ExecutionResult
from textgrid_tools_cli.helper import (add_directory_argument, add_encoding_argument,
                                       add_n_digits_argument, add_output_directory_argument,
                                       add_overwrite_argument, get_audio_files, get_files_dict,
                                       get_optional, get_text_files, parse_existing_directory,
                                       parse_non_empty_or_whitespace, parse_positive_float,
                                       read_audio, save_grid, try_load_grid)

DEFAULT_CHARACTERS_PER_SECOND = 15
META_FILE_TYPE = ".meta"


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
  add_encoding_argument(parser, "encoding of text and meta files")
  parser.add_argument("--speech-rate", type=parse_positive_float, default=DEFAULT_CHARACTERS_PER_SECOND, metavar='SPEED',
                      help="the speech rate (characters per second) which should be used to calculate the duration of the grids if no corresponding audio file exists")
  add_n_digits_argument(parser)
  add_output_directory_argument(parser)
  add_overwrite_argument(parser)
  return app_create_grid_from_text


def process_read_text(item: Tuple[str, Path], encoding: str) -> Optional[str]:
  stem, path = item
  try:
    return stem, path.read_text(encoding)
  except Exception as ex:
    return stem, None


def process_read_audiodata(item: Tuple[str, Path]) -> Optional[Tuple[int, int]]:
  stem, path = item
  try:
    sample_rate, audio_in = read_audio(path)
  except Exception as ex:
    return stem, None
  audio_samples_in = audio_in.shape[0]
  return stem, (sample_rate, audio_samples_in)


def process_save_grid(item: Tuple[Path, TextGrid]) -> None:
  grid_file_out_abs, grid = item
  if grid is None:
    return
  try:
    save_grid(grid_file_out_abs, grid)
  except Exception as ex:
    pass


def app_create_grid_from_text(directory: Path, audio_directory: Optional[Path], meta_directory: Optional[Path], name: Optional[str], tier: str, speech_rate: float, n_digits: int, output_directory: Optional[Path], encoding: str, overwrite: bool) -> ExecutionResult:
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

  keys = OrderedSet(text_files.keys())

  chunk_size = 1000
  chunked_list = (keys[i:i + chunk_size] for i in range(0, len(keys), chunk_size))
  total_success = True
  n_jobs = 1
  maxtasksperchild = None
  chunksize = 10

  read_method_proxy = partial(
    process_read_text,
    encoding=encoding,
  )

  chunk: OrderedSet[str]
  for chunk in tqdm(chunked_list, desc="Processing chunks", unit="chunk(s)"):
    process_data = (
      (stem, directory / text_files[stem])
      for stem in chunk
    )

    with ThreadPool(
      processes=n_jobs,
    ) as pool:
      iterator = pool.imap_unordered(read_method_proxy, process_data, chunksize)
      iterator = tqdm(iterator, total=len(chunk),
                      desc="Reading text files", unit="file(s)")
      parsed_text_files = dict(iterator)
    del process_data

    relevant_audio_files = chunk.intersection(audio_files.keys())
    process_data = (
      (stem, audio_directory / audio_files[stem])
      for stem in relevant_audio_files
    )

    with ThreadPool(
      processes=n_jobs,
    ) as pool:
      iterator = pool.imap_unordered(process_read_audiodata, process_data, chunksize)
      iterator = tqdm(iterator, total=len(relevant_audio_files),
                      desc="Reading audio files", unit="file(s)")
      parsed_audio_files = dict(iterator)
    del process_data

    relevant_meta_files = chunk.intersection(meta_files.keys())
    process_data = (
      (stem, meta_directory / meta_files[stem])
      for stem in relevant_meta_files
    )

    with ThreadPool(
      processes=n_jobs,
    ) as pool:
      iterator = pool.imap_unordered(read_method_proxy, process_data, chunksize)
      iterator = tqdm(iterator, total=len(relevant_meta_files),
                      desc="Reading meta files", unit="file(s)")
      parsed_meta_files = dict(iterator)
    del process_data

    created_grids = dict.fromkeys(parsed_text_files.keys(), None)
    for file_stem, text in tqdm(parsed_text_files.items(), desc="Processing", unit="file(s)"):
      if text is None:
        continue
      sample_rate = None
      audio_samples_in = None
      audio_data = parsed_audio_files.get(file_stem, None)
      if audio_data is not None:
        sample_rate, audio_samples_in = audio_data

      meta = parsed_meta_files.get(file_stem, None)

      (error, _), grid = create_grid_from_text(text, meta, audio_samples_in,
                                               sample_rate, name, tier, speech_rate, n_digits)

      success = error is None
      total_success &= success
      if success:
        created_grids[file_stem] = grid
      else:
        created_grids.pop(file_stem)
        logger.error(error.default_message)
        logger.info("Skipped.")

    save_files = (
      (output_directory / f"{stem}.TextGrid", grid)
      for stem, grid in created_grids.items()
    )

    with ThreadPool(
      processes=n_jobs,
    ) as pool:
      iterator = pool.imap_unordered(process_save_grid, save_files, chunksize)
      iterator = tqdm(iterator, total=len(created_grids), desc="Saving files", unit="file(s)")
      list(iterator)

  return total_success, True
