import argparse
import codecs
import os
import re
from argparse import ArgumentParser, ArgumentTypeError
from collections import OrderedDict
from functools import partial
from os import cpu_count
from pathlib import Path
from shutil import copy
from typing import Callable, Generator, List, Optional
from typing import OrderedDict as OrderedDictType
from typing import Set, Tuple, TypeVar

import numpy as np
from ordered_set import OrderedSet
from scipy.io.wavfile import read, write
from textgrid import TextGrid

from textgrid_tools.helper import check_is_valid_grid
from textgrid_tools_cli.globals import (DEFAULT_ENCODING, DEFAULT_MAXTASKSPERCHILD,
                                        DEFAULT_N_FILE_CHUNKSIZE, DEFAULT_N_JOBS)
from textgrid_tools_cli.textgrid_io import read_file_faster, save_file_faster
from textgrid_tools_cli.validation import GridCouldNotBeLoadedError, GridCouldNotBeSavedError

GRID_FILE_TYPE = ".TextGrid"
TXT_FILE_TYPE = ".txt"
WAV_FILE_TYPE = ".wav"
MP3_FILE_TYPE = ".mp3"


def get_chunks(keys: OrderedSet[str], chunk_size: Optional[int]) -> List[OrderedSet[str]]:
  if chunk_size is None:
    chunk_size = len(keys)
  chunked_list = list(keys[i: i + chunk_size] for i in range(0, len(keys), chunk_size))
  return chunked_list


def get_files_dict(directory: Path, filetypes: Set[str]) -> OrderedDictType[str, Path]:
  result = OrderedDict(sorted(get_files_tuples(directory, filetypes)))
  return result


def get_files_tuples(directory: Path, filetypes: Set[str]) -> Generator[Tuple[str, Path], None, None]:
  filetypes_lower = {ft.lower() for ft in filetypes}
  all_files = get_all_files_in_all_subfolders(directory)
  resulting_files = (
    (str(file.relative_to(directory).parent / file.stem), file.relative_to(directory))
      for file in all_files if file.suffix.lower() in filetypes_lower
  )
  return resulting_files


def get_all_files_in_all_subfolders(directory: Path) -> Generator[Path, None, None]:
  for root, _, files in os.walk(directory):
    for name in files:
      file_path = Path(root) / name
      yield file_path


def get_files_in_folder(directory: Path) -> Generator[Path, None, None]:
  root, _, files = next(os.walk(directory))
  for name in files:
    file_path = Path(root) / name
    yield file_path


def get_subfolders(directory: Path) -> Generator[Path, None, None]:
  root, folders, _ = next(os.walk(directory))
  for name in folders:
    file_path = Path(root) / name
    yield file_path


class ConvertToOrderedSetAction(argparse._StoreAction):
  def __call__(self, parser: argparse.ArgumentParser, namespace: argparse.Namespace, values: Optional[List], option_string: Optional[str] = None):
    if values is not None:
      values = OrderedSet(values)
    super().__call__(parser, namespace, values, option_string)


def add_n_digits_argument(parser: ArgumentParser) -> None:
  parser.add_argument("--n-digits", type=int, default=16, metavar='COUNT',
                      choices=range(17), help="precision of the grids (max count of digits after the comma)")


# class CheckFileAlreadyExistNoOverride(argparse._StoreAction):
#   def __call__(self, parser: argparse.ArgumentParser, namespace: argparse.Namespace, values: Optional[Path], option_string: Optional[str] = None):
#     if values is not None:
#       if not namespace.overwrite and values.is_file():
#         raise ArgumentTypeError("File already exists!")
#     super().__call__(parser, namespace, values, option_string)


def add_encoding_argument(parser: ArgumentParser, help_str: str = "encoding of the grid files") -> None:
  parser.add_argument("--encoding", type=parse_codec, metavar='CODEC',
                      help=help_str + "; see all available codecs at https://docs.python.org/3.8/library/codecs.html#standard-encodings", default=DEFAULT_ENCODING)


def add_overwrite_argument(parser: ArgumentParser) -> None:
  parser.add_argument("-o", "--overwrite", action="store_true",
                      help="overwrite existing files")


def add_output_directory_argument(parser: ArgumentParser) -> None:
  parser.add_argument("-out", "--output-directory", metavar='OUTPUT-PATH', type=get_optional(parse_path),
                      help="directory where to output the grids if not to the same directory")


def add_directory_argument(parser: ArgumentParser, help_str: str = "directory containing the grids") -> None:
  parser.add_argument("directory", type=parse_existing_directory, metavar="DIRECTORY",
                      help=help_str)


def add_tiers_argument(parser: ArgumentParser, help_str: str, meta_var: str = "TIER") -> None:
  parser.add_argument("tiers", metavar=meta_var, type=parse_non_empty_or_whitespace,
                      nargs="+", help=help_str, action=ConvertToOrderedSetAction)


def add_tier_argument(parser: ArgumentParser, help_str: str, meta_var: str = "TIER") -> None:
  parser.add_argument("tier", metavar=meta_var, type=parse_non_empty_or_whitespace, help=help_str)

# def add_overwrite_tier_argument(parser: ArgumentParser) -> None:
#   parser.add_argument("-ot", "--overwrite-tier", action="store_true",
#                       help="overwrite existing tiers")


def add_n_jobs_argument(parser: ArgumentParser) -> None:
  parser.add_argument("-j", "--n-jobs", metavar='N', type=int,
                      choices=range(1, cpu_count() + 1), default=DEFAULT_N_JOBS, help="amount of parallel cpu jobs")


def add_dry_run_argument(parser: ArgumentParser) -> None:
  parser.add_argument("-d", "--dry", action="store_true",
                      help="dry run (i.e., don't change anything)")


T = TypeVar("T")


def parse_codec(value: str) -> str:
  value = parse_required(value)
  try:
    codecs.lookup(value)
  except LookupError as error:
    raise ArgumentTypeError("Codec was not found!") from error
  return value


def parse_path(value: str) -> Path:
  value = parse_required(value)
  try:
    path = Path(value)
  except ValueError as error:
    raise ArgumentTypeError("Value needs to be a path!") from error
  return path


def parse_txt_path(value: str) -> Path:
  value = parse_path(value)
  if value.suffix.lower() != ".txt":
    raise ArgumentTypeError("Value needs to be a .txt path!")
  return value


def parse_optional_value(value: str, method: Callable[[str], T]) -> Optional[T]:
  if value is None:
    return None
  return method(value)


def get_optional(method: Callable[[str], T]) -> Callable[[str], Optional[T]]:
  result = partial(
    parse_optional_value,
    method=method,
  )
  return result


def parse_existing_file(value: str) -> Path:
  path = parse_path(value)
  if not path.is_file():
    raise ArgumentTypeError("File was not found!")
  return path


def parse_existing_directory(value: str) -> Path:
  path = parse_path(value)
  if not path.is_dir():
    raise ArgumentTypeError("Directory was not found!")
  return path


def parse_required(value: Optional[str]) -> str:
  if value is None:
    raise ArgumentTypeError("Value must not be None!")
  return value


def parse_non_empty(value: Optional[str]) -> str:
  value = parse_required(value)
  if value == "":
    raise ArgumentTypeError("Value must not be empty!")
  return value


def parse_pattern(value: Optional[str]) -> re.Pattern:
  value = parse_required(value)
  try:
    result = re.compile(value)
  except re.error as error:
    raise ArgumentTypeError("Value needs to be a valid pattern!") from error
  return result


def parse_non_empty_or_whitespace(value: str) -> str:
  value = parse_required(value)
  if value.strip() == "":
    raise ArgumentTypeError("Value must not be empty or whitespace!")
  return value


def parse_float(value: str) -> float:
  value = parse_required(value)
  try:
    value = float(value)
  except ValueError as error:
    raise ArgumentTypeError("Value needs to be a decimal number!") from error
  return value


def parse_positive_float(value: str) -> float:
  value = parse_float(value)
  if not value > 0:
    raise ArgumentTypeError("Value needs to be greater than zero!")
  return value


def parse_non_negative_float(value: str) -> float:
  value = parse_float(value)
  if not value >= 0:
    raise ArgumentTypeError("Value needs to be greater than or equal to zero!")
  return value


def parse_integer(value: str) -> int:
  value = parse_required(value)
  if not value.isdigit():
    raise ArgumentTypeError("Value needs to be an integer!")
  value = int(value)
  return value


def parse_positive_integer(value: str) -> int:
  value = parse_integer(value)
  if not value > 0:
    raise ArgumentTypeError("Value needs to be greater than zero!")
  return value


def parse_non_negative_integer(value: str) -> int:
  value = parse_integer(value)
  if not value >= 0:
    raise ArgumentTypeError("Value needs to be greater than or equal to zero!")
  return value


def add_chunksize_argument(parser: ArgumentParser, target: str = "files", default: int = DEFAULT_N_FILE_CHUNKSIZE) -> None:
  parser.add_argument("-s", "--chunksize", type=parse_positive_integer, metavar="NUMBER",
                      help=f"amount of {target} to chunk into one job", default=default)


def add_maxtaskperchild_argument(parser: ArgumentParser) -> None:
  parser.add_argument("-m", "--maxtasksperchild", type=get_optional(parse_positive_integer), metavar="NUMBER",
                      help="amount of tasks per child", default=DEFAULT_MAXTASKSPERCHILD)


def get_grid_files(folder: Path) -> OrderedDictType[str, Path]:
  result = get_files_dict(folder, filetypes={GRID_FILE_TYPE})
  # logger = getLogger(__name__)
  # logger.info(f"Found {len(result)} grid files.")
  return result


def get_audio_files(folder: Path) -> OrderedDictType[str, Path]:
  result = get_files_dict(folder, filetypes={WAV_FILE_TYPE})
  # logger = getLogger(__name__)
  # logger.info(f"Found {len(result)} audio files.")
  return result


def get_text_files(folder: Path) -> OrderedDictType[str, Path]:
  result = get_files_dict(folder, filetypes={TXT_FILE_TYPE})
  # logger = getLogger(__name__)
  # logger.info(f"Found {len(result)} text files.")
  return result


def try_load_grid(path: Path, encoding: str = "UTF-8") -> Tuple[Optional[GridCouldNotBeLoadedError], Optional[TextGrid]]:
  try:
    grid_in = read_file_faster(path, encoding)
  except Exception as ex:
    #logger = getLogger(__name__)
    # logger.debug(ex)
    return GridCouldNotBeLoadedError(path, ex), None
  return None, grid_in


def try_save_grid(path: Path, grid: TextGrid, encoding: str = "UTF-8") -> Optional[GridCouldNotBeLoadedError]:
  try:
    save_grid(path, grid, encoding)
  except Exception as ex:
    return GridCouldNotBeSavedError(path, ex)
  return None


def try_copy_grid(grid_in: Path, grid_out: Path) -> Optional[GridCouldNotBeLoadedError]:
  try:
    copy_grid(grid_in, grid_out)
  except Exception as ex:
    return GridCouldNotBeSavedError(grid_out, ex)
  return None


def save_grid(path: Path, grid: TextGrid, encoding: str = "UTF-8") -> None:
  assert check_is_valid_grid(grid)
  path.parent.mkdir(exist_ok=True, parents=True)
  save_file_faster(grid, path, encoding)


def copy_grid(grid_in: Path, grid_out: Path) -> None:
  #logger = getLogger(__name__)
  #logger.debug("Copying grid...")
  copy_file(grid_in, grid_out)


def copy_audio(audio_in: Path, audio_out: Path) -> None:
  #logger = getLogger(__name__)
  #logger.debug("Copying audio...")
  copy_file(audio_in, audio_out)


def copy_file(file_in: Path, file_out: Path) -> None:
  file_out.parent.mkdir(exist_ok=True, parents=True)
  copy(file_in, file_out)


def save_text(path: Path, text: str, encoding: str) -> None:
  #logger = getLogger(__name__)
  #logger.debug("Saving text...")
  path.parent.mkdir(parents=True, exist_ok=True)
  path.write_text(text, encoding=encoding)


def save_audio(path: Path, audio: np.ndarray, sampling_rate: int) -> None:
  path.parent.mkdir(exist_ok=True, parents=True)
  write(path, sampling_rate, audio)


def read_audio(path: Path) -> Tuple[int, np.ndarray]:
  # assert not MP3_FILE_TYPE in path.name:
    # audio_in, sample_rate = librosa.load(audio_file_in_abs)
    # with audioread.audio_open(audio_file_in_abs) as f:
    #   sample_rate = f.samplerate
    #   x = f.read_data()
    #   import numpy as np
    #   y = np.frombuffer(x)
    #   audio_in = f
  assert WAV_FILE_TYPE.lower() == path.suffix.lower()
  sample_rate, audio_in = read(path)
  return sample_rate, audio_in
