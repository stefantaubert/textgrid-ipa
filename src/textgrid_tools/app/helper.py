from collections import OrderedDict
from pathlib import Path
from typing import OrderedDict as OrderedDictType
from typing import Set, Tuple

import numpy as np
from general_utils.main import get_all_files_in_all_subfolders
from scipy.io.wavfile import read, write
from textgrid.textgrid import TextGrid

GRID_FILE_TYPE = ".TextGrid"
TXT_FILE_TYPE = ".txt"
WAV_FILE_TYPE = ".wav"
MP3_FILE_TYPE = ".mp3"


def get_grid_files(folder: Path) -> OrderedDictType[str, Path]:
  return get_files_dict(folder, filetypes={GRID_FILE_TYPE})


def get_audio_files(folder: Path) -> OrderedDictType[str, Path]:
  return get_files_dict(folder, filetypes={WAV_FILE_TYPE, MP3_FILE_TYPE})


def get_text_files(folder: Path) -> OrderedDictType[str, Path]:
  return get_files_dict(folder, filetypes={TXT_FILE_TYPE})


def get_files_dict(folder: Path, filetypes: Set[str]) -> OrderedDictType[str, Path]:
  filetypes_lower = {ft.lower() for ft in filetypes}
  all_files = get_all_files_in_all_subfolders(folder)
  resulting_files = (
    (str(file.relative_to(folder).parent / file.stem), file.relative_to(folder))
      for file in all_files if file.suffix.lower() in filetypes_lower
  )
  result = OrderedDict(resulting_files)
  return result


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
    assert WAV_FILE_TYPE in path
    sample_rate, audio_in = read(path)
    return sample_rate, audio_in
