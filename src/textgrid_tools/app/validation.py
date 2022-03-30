from pathlib import Path
from typing import Optional

from textgrid import TextGrid
from textgrid_tools.core import ValidationError as ValidationErrorCore


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
  def __init__(self, path: Path) -> None:
      super().__init__()
      self.path = path
  # @classmethod
  # def validate(cls, grid: Optional[TextGrid]):
  #   if not (grid is not None):
  #     return cls()
  #   return None

  @property
  def default_message(self) -> str:
    return f"Grid '{self.path.absolute()}' couldn't be loaded!"
