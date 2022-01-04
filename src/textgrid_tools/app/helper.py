from argparse import ArgumentParser
from collections import OrderedDict
from os import cpu_count
from pathlib import Path
from typing import OrderedDict as OrderedDictType
from typing import Set, Tuple

import numpy as np
from general_utils.main import get_files_dict
from scipy.io.wavfile import read, write
from textgrid.textgrid import TextGrid
from textgrid_tools.app.globals import DEFAULT_N_DIGITS, DEFAULT_N_JOBS

GRID_FILE_TYPE = ".TextGrid"
TXT_FILE_TYPE = ".txt"
WAV_FILE_TYPE = ".wav"
MP3_FILE_TYPE = ".mp3"


def add_n_digits_argument(parser: ArgumentParser) -> None:
  parser.add_argument("--n-digits", type=int, default=DEFAULT_N_DIGITS, metavar='N',
                      choices=range(17), help="precision of the grid files (max count of digits after the comma)")


def add_overwrite_argument(parser: ArgumentParser) -> None:
  parser.add_argument("-o", "--overwrite", action="store_true",
                      help="overwrite existing files")


def add_overwrite_tier_argument(parser: ArgumentParser) -> None:
  parser.add_argument("-ot", "--overwrite-tier", action="store_true",
                      help="overwrite existing tiers")


def add_n_jobs_argument(parser: ArgumentParser) -> None:
  parser.add_argument("-j", "--n-jobs", metavar='N', type=int,
                      choices=range(1, cpu_count() + 1), default=DEFAULT_N_JOBS, help="amount of parallel cpu jobs")


def get_grid_files(folder: Path) -> OrderedDictType[str, Path]:
  return get_files_dict(folder, filetypes={GRID_FILE_TYPE})


def get_audio_files(folder: Path) -> OrderedDictType[str, Path]:
  return get_files_dict(folder, filetypes={WAV_FILE_TYPE})


def get_text_files(folder: Path) -> OrderedDictType[str, Path]:
  return get_files_dict(folder, filetypes={TXT_FILE_TYPE})


def load_grid(path: Path, n_digits: int) -> TextGrid:
  grid_in = TextGrid()
  grid_in.read(path, round_digits=n_digits)
  return grid_in


def save_grid(path: Path, grid: TextGrid) -> None:
  path.parent.mkdir(exist_ok=True, parents=True)
  grid.write(path)


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
