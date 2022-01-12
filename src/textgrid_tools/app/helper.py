from argparse import ArgumentParser
from logging import getLogger
from os import cpu_count
from pathlib import Path
from shutil import copy
from typing import OrderedDict as OrderedDictType
from typing import Tuple

import numpy as np
from general_utils.main import get_files_dict
from scipy.io.wavfile import read, write
from text_utils.string_format import StringFormat
from textgrid.textgrid import TextGrid
from textgrid_tools.app.globals import (DEFAULT_ENCODING, DEFAULT_N_DIGITS,
                                        DEFAULT_N_JOBS)
from textgrid_tools.core.interval_format import IntervalFormat

GRID_FILE_TYPE = ".TextGrid"
TXT_FILE_TYPE = ".txt"
WAV_FILE_TYPE = ".wav"
MP3_FILE_TYPE = ".mp3"


def add_n_digits_argument(parser: ArgumentParser) -> None:
  parser.add_argument("--n-digits", type=int, default=DEFAULT_N_DIGITS, metavar='COUNT',
                      choices=range(17), help="precision of the grids (max count of digits after the comma)")


def add_string_format_argument(parser: ArgumentParser, name: str = '--tier-format', help_str: str = "format of tier") -> None:
  parser.add_argument(name, choices=StringFormat,
                      type=StringFormat.__getitem__, default=StringFormat.TEXT, help=help_str)


def add_interval_format_argument(parser: ArgumentParser, name: str, help_str: str) -> None:
  parser.add_argument(name, choices=IntervalFormat,
                      type=IntervalFormat.__getitem__, default=IntervalFormat.WORD, help=help_str)


def add_encoding_argument(parser: ArgumentParser, help_str: str) -> None:
  parser.add_argument("--encoding", type=str, metavar='ENCODING',
                      help=help_str, default=DEFAULT_ENCODING)


def add_overwrite_argument(parser: ArgumentParser) -> None:
  parser.add_argument("-o", "--overwrite", action="store_true",
                      help="overwrite existing files")


def add_output_directory_argument(parser: ArgumentParser) -> None:
  parser.add_argument("--output-directory", metavar='PATH', type=Path,
                      help="directory where to output the grids if not to the same directory")


def add_grid_directory_argument(parser: ArgumentParser) -> None:
  parser.add_argument("directory", type=Path, metavar="directory",
                      help="directory containing the grids")


# def add_overwrite_tier_argument(parser: ArgumentParser) -> None:
#   parser.add_argument("-ot", "--overwrite-tier", action="store_true",
#                       help="overwrite existing tiers")


def add_n_jobs_argument(parser: ArgumentParser) -> None:
  parser.add_argument("-j", "--n-jobs", metavar='N', type=int,
                      choices=range(1, cpu_count() + 1), default=DEFAULT_N_JOBS, help="amount of parallel cpu jobs")


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


def load_grid(path: Path, n_digits: int) -> TextGrid:
  grid_in = TextGrid()
  grid_in.read(path, round_digits=n_digits)
  return grid_in


def save_grid(path: Path, grid: TextGrid) -> None:
  logger = getLogger(__name__)
  logger.info("Saving grid...")
  path.parent.mkdir(exist_ok=True, parents=True)
  grid.write(path)


def copy_grid(grid_in: Path, grid_out: Path) -> None:
  logger = getLogger(__name__)
  logger.info("Copying grid...")
  copy_file(grid_in, grid_out)


def copy_audio(audio_in: Path, audio_out: Path) -> None:
  logger = getLogger(__name__)
  logger.info("Copying audio...")
  copy_file(audio_in, audio_out)


def copy_file(file_in: Path, file_out: Path) -> None:
  file_out.parent.mkdir(exist_ok=True, parents=True)
  copy(file_in, file_out)


def save_text(path: Path, text: str, encoding: str) -> None:
  logger = getLogger(__name__)
  logger.info("Saving text...")
  path.parent.mkdir(parents=True, exist_ok=True)
  path.write_text(text, encoding=encoding)


def save_audio(path: Path, audio: np.ndarray, sampling_rate: int) -> None:
  path.parent.mkdir(exist_ok=True, parents=True)
  write(path, sampling_rate, audio)


def read_audio(path: Path) -> Tuple[int, np.ndarray]:
  if MP3_FILE_TYPE in path.name:
    raise Exception()
    #audio_in, sample_rate = librosa.load(audio_file_in_abs)
    # with audioread.audio_open(audio_file_in_abs) as f:
    #   sample_rate = f.samplerate
    #   x = f.read_data()
    #   import numpy as np
    #   y = np.frombuffer(x)
    #   audio_in = f
  else:
    assert WAV_FILE_TYPE in path.name
    sample_rate, audio_in = read(path)
    return sample_rate, audio_in
