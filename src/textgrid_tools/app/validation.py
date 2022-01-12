from pathlib import Path

from textgrid_tools.core.validation import \
    ValidationError as ValidationErrorCore


class ValidationError(ValidationErrorCore):
  pass


class DirectoryNotExistsError(ValidationError):
  def __init__(self, directory: Path) -> None:
    super().__init__()
    self.directory = directory

  @classmethod
  def validate(cls, directory: Path):
    if not directory.exists():
      return cls(directory)
    return None

  @property
  def default_message(self) -> str:
    return f"Directory \"{str(self.directory)}\" does not exist!"


class FileAlreadyExistsError(ValidationError):
  def __init__(self, path: Path) -> None:
    super().__init__()
    self.path = path

  @classmethod
  def validate(cls, path: Path):
    if not path.exists():
      return cls(path)
    return None

  @property
  def default_message(self) -> str:
    return f"File \"{str(self.path)}\" does already exist!"


class FileNotExistsError(ValidationError):
  def __init__(self, path: Path) -> None:
    super().__init__()
    self.path = path

  @classmethod
  def validate(cls, path: Path):
    if not path.exists():
      return cls(path)
    return None

  @property
  def default_message(self) -> str:
    return f"File \"{str(self.path)}\" does not exist!"
