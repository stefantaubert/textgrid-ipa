from collections import OrderedDict
from pathlib import Path
from typing import OrderedDict as OrderedDictType
from typing import Set

from general_utils.main import get_all_files_in_all_subfolders
from textgrid.textgrid import TextGrid

GRID_FILE_TYPE = ".TextGrid"
TXT_FILE_TYPE = ".txt"
WAV_FILE_TYPE = ".wav"
# MP3_FILE_TYPE = ".mp3"


def get_grid_files(folder: Path) -> OrderedDictType[str, Path]:
  return get_files_dict(folder, filetypes={GRID_FILE_TYPE})


def get_audio_files(folder: Path) -> OrderedDictType[str, Path]:
  return get_files_dict(folder, filetypes={WAV_FILE_TYPE})


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
