from pathlib import Path
from typing import Optional

from textgrid import TextGrid
from textgrid_tools import ValidationError as ValidationErrorCore


class ValidationError(ValidationErrorCore):
  pass


class FileAlreadyExistsError(ValidationError):
  def __init__(self, path: Path) -> None:
    super().__init__()
    self.path = path

  @classmethod
  def validate(cls, path: Path):
    if path.is_file():
      return cls(path)
    return None

  @property
  def default_message(self) -> str:
    return f"File \"{str(self.path.absolute())}\" does already exist!"


class GridCouldNotBeLoadedError(ValidationError):
  def __init__(self, path: Path, exception: Exception) -> None:
    super().__init__()
    self.path = path
    self.exception = exception

  @property
  def default_message(self) -> str:
    return f"Grid couldn't be loaded!"
