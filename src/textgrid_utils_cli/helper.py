import argparse
import codecs
from argparse import ArgumentParser, ArgumentTypeError
from collections import OrderedDict
from functools import partial
from logging import getLogger
from os import cpu_count
from pathlib import Path
from shutil import copy
from typing import Callable, List, Optional
from typing import OrderedDict as OrderedDictType
from typing import Tuple, TypeVar

import numpy as np
from general_utils.main import get_files_dict
from ordered_set import OrderedSet
from scipy.io.wavfile import read, write
from text_utils import Language, SymbolFormat
from text_utils.string_format import StringFormat
from textgrid.textgrid import TextGrid
from textgrid_utils_cli.globals import (DEFAULT_ENCODING,
                                        DEFAULT_MAXTASKSPERCHILD,
                                        DEFAULT_N_DIGITS,
                                        DEFAULT_N_FILE_CHUNKSIZE,
                                        DEFAULT_N_JOBS)
from textgrid_utils_cli.validation import GridCouldNotBeLoadedError
from textgrid_utils.helper import check_is_valid_grid
from textgrid_utils.interval_format import IntervalFormat

GRID_FILE_TYPE = ".TextGrid"
TXT_FILE_TYPE = ".txt"
WAV_FILE_TYPE = ".wav"
MP3_FILE_TYPE = ".mp3"


class ConvertToOrderedSetAction(argparse._StoreAction):
  def __call__(self, parser: argparse.ArgumentParser, namespace: argparse.Namespace, values: Optional[List], option_string: Optional[str] = None):
    if values is not None:
      values = OrderedSet(values)
    super().__call__(parser, namespace, values, option_string)


def add_n_digits_argument(parser: ArgumentParser) -> None:
  parser.add_argument("--n-digits", type=int, default=DEFAULT_N_DIGITS, metavar='COUNT',
                      choices=range(17), help="precision of the grids (max count of digits after the comma)")


# class CheckFileAlreadyExistNoOverride(argparse._StoreAction):
#   def __call__(self, parser: argparse.ArgumentParser, namespace: argparse.Namespace, values: Optional[Path], option_string: Optional[str] = None):
#     if values is not None:
#       if not namespace.overwrite and values.is_file():
#         raise ArgumentTypeError("File already exists!")
#     super().__call__(parser, namespace, values, option_string)

def add_string_format_argument(parser: ArgumentParser, target: str, short_name: str = "-f", name: str = '--formatting') -> None:
  names = OrderedDict((
    (StringFormat.TEXT, "Normal"),
    (StringFormat.SYMBOLS, "Spaced"),
  ))

  values_to_names = dict(zip(
    names.values(),
    names.keys()
  ))

  help_str = f"formatting of text in {target}; use \'{names[StringFormat.TEXT]}\' for normal text and \'{names[StringFormat.SYMBOLS]}\' for space separated symbols, i.e., words are separated by two spaces and characters are separated by one space. Example: {names[StringFormat.TEXT]} -> |This text.|; {names[StringFormat.SYMBOLS]} -> |T␣h␣i␣s␣␣t␣e␣x␣t␣.|"
  parser.add_argument(
    short_name, name,
    metavar=list(names.values()),
    choices=StringFormat,
    type=values_to_names.get,
    default=names[StringFormat.TEXT],
    help=help_str,
  )


def add_interval_format_argument(parser: ArgumentParser, target: str, short_name: str = "-c", name: str = '--content') -> None:
  names = OrderedDict((
    (IntervalFormat.SYMBOL, "Symbol"),
    (IntervalFormat.SYMBOLS, "Symbols"),
    (IntervalFormat.WORD, "Word"),
    (IntervalFormat.WORDS, "Words"),
  ))

  values_to_names = dict(zip(
    names.values(),
    names.keys()
  ))

  help_str = f"type of intervals content in {target}, i.e., what does one interval contain if it is not a pause-interval? Example: {names[IntervalFormat.SYMBOL]} -> |AA1|B|CH|; {names[IntervalFormat.SYMBOLS]} -> |\"␣AA0|B|CH␣.|; {names[IntervalFormat.WORD]} -> |This|is|a|sentence.|; {names[IntervalFormat.WORDS]} -> |This␣is␣a␣sentence.|And␣another␣one.|"
  parser.add_argument(
    short_name, name,
    metavar=list(names.values()),
    choices=IntervalFormat,
    type=values_to_names.get,
    default=names[IntervalFormat.WORDS],
    help=help_str,
  )


def add_language_argument(parser: ArgumentParser, target: str, short_name: str = "-l", name: str = '--language') -> None:
  names = OrderedDict((
    (Language.ENG, "en"),
    (Language.GER, "de"),
    (Language.CHN, "zh"),
  ))

  values_to_names = dict(zip(
    names.values(),
    names.keys()
  ))

  help_str = f"language of {target} (ISO 639-1 Code)"
  parser.add_argument(
    short_name, name,
    metavar=list(names.values()),
    choices=Language,
    type=values_to_names.get,
    default=names[Language.ENG],
    help=help_str,
  )


def add_symbol_format(parser: ArgumentParser, target: str, short_name: str = "-sf", name: str = '--symbol-format') -> None:
  names = OrderedDict((
    (SymbolFormat.GRAPHEMES, "Graphemes"),
    (SymbolFormat.PHONEMES_ARPA, "ARPA-Phonemes"),
    (SymbolFormat.PHONEMES_IPA, "IPA-Phonemes"),
    (SymbolFormat.PHONES_IPA, "IPA-Phones"),
  ))

  values_to_names = dict(zip(
    names.values(),
    names.keys()
  ))

  help_str = f"format of symbols in {target}"
  parser.add_argument(
    short_name, name,
    metavar=list(names.values()),
    choices=SymbolFormat,
    type=values_to_names.get,
    default=names[SymbolFormat.GRAPHEMES],
    help=help_str,
  )


def add_encoding_argument(parser: ArgumentParser, help_str: str) -> None:
  parser.add_argument("--encoding", type=parse_codec, metavar='CODEC',
                      help=help_str + "; see all available codecs at https://docs.python.org/3.8/library/codecs.html#standard-encodings", default=DEFAULT_ENCODING)


def add_overwrite_argument(parser: ArgumentParser) -> None:
  parser.add_argument("-o", "--overwrite", action="store_true",
                      help="overwrite existing files")


def add_output_directory_argument(parser: ArgumentParser) -> None:
  parser.add_argument("-out", "--output-directory", metavar='PATH', type=get_optional(parse_path),
                      help="directory where to output the grids if not to the same directory")


def add_directory_argument(parser: ArgumentParser, help_str: str = "directory containing the grids") -> None:
  parser.add_argument("directory", type=parse_existing_directory, metavar="directory",
                      help=help_str)


def add_tiers_argument(parser: ArgumentParser, help_str: str) -> None:
  parser.add_argument("tiers", metavar="tiers", type=parse_non_empty_or_whitespace,
                      nargs="+", help=help_str, action=ConvertToOrderedSetAction)


def add_tier_argument(parser: ArgumentParser, help_str: str) -> None:
  parser.add_argument("tier", metavar="tier", type=parse_non_empty_or_whitespace, help=help_str)

# def add_overwrite_tier_argument(parser: ArgumentParser) -> None:
#   parser.add_argument("-ot", "--overwrite-tier", action="store_true",
#                       help="overwrite existing tiers")


def add_n_jobs_argument(parser: ArgumentParser) -> None:
  parser.add_argument("-j", "--n-jobs", metavar='N', type=int,
                      choices=range(1, cpu_count() + 1), default=DEFAULT_N_JOBS, help="amount of parallel cpu jobs")


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
  logger = getLogger(__name__)
  logger.info(f"Found {len(result)} grid files.")
  return result


def get_audio_files(folder: Path) -> OrderedDictType[str, Path]:
  result = get_files_dict(folder, filetypes={WAV_FILE_TYPE})
  logger = getLogger(__name__)
  logger.info(f"Found {len(result)} audio files.")
  return result


def get_text_files(folder: Path) -> OrderedDictType[str, Path]:
  result = get_files_dict(folder, filetypes={TXT_FILE_TYPE})
  logger = getLogger(__name__)
  logger.info(f"Found {len(result)} text files.")
  return result


def try_load_grid(path: Path, n_digits: int) -> Tuple[Optional[GridCouldNotBeLoadedError], Optional[TextGrid]]:
  grid_in = TextGrid()
  try:
    grid_in.read(path, round_digits=n_digits)
  except Exception as ex:
    logger = getLogger(__name__)
    logger.debug(ex)
    return GridCouldNotBeLoadedError(path, ex), None
  return None, grid_in


def save_grid(path: Path, grid: TextGrid) -> None:
  logger = getLogger(__name__)
  logger.debug("Saving grid...")
  assert check_is_valid_grid(grid)
  path.parent.mkdir(exist_ok=True, parents=True)
  grid.write(path)


def copy_grid(grid_in: Path, grid_out: Path) -> None:
  logger = getLogger(__name__)
  logger.debug("Copying grid...")
  copy_file(grid_in, grid_out)


def copy_audio(audio_in: Path, audio_out: Path) -> None:
  logger = getLogger(__name__)
  logger.debug("Copying audio...")
  copy_file(audio_in, audio_out)


def copy_file(file_in: Path, file_out: Path) -> None:
  file_out.parent.mkdir(exist_ok=True, parents=True)
  copy(file_in, file_out)


def save_text(path: Path, text: str, encoding: str) -> None:
  logger = getLogger(__name__)
  logger.debug("Saving text...")
  path.parent.mkdir(parents=True, exist_ok=True)
  path.write_text(text, encoding=encoding)


def save_audio(path: Path, audio: np.ndarray, sampling_rate: int) -> None:
  path.parent.mkdir(exist_ok=True, parents=True)
  write(path, sampling_rate, audio)


def read_audio(path: Path) -> Tuple[int, np.ndarray]:
  # assert not MP3_FILE_TYPE in path.name:
    #audio_in, sample_rate = librosa.load(audio_file_in_abs)
    # with audioread.audio_open(audio_file_in_abs) as f:
    #   sample_rate = f.samplerate
    #   x = f.read_data()
    #   import numpy as np
    #   y = np.frombuffer(x)
    #   audio_in = f
  assert WAV_FILE_TYPE.lower() == path.suffix.lower()
  sample_rate, audio_in = read(path)
  return sample_rate, audio_in
