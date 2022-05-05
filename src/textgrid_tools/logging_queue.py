from logging import LogRecord
from typing import Generator


class LoggingQueue():
  """helper class to stack logs for a grid file"""

  def __init__(self, name: str) -> None:
    self.name = name
    self.__records = []

  def log(self, level, msg, args=None, exc_info=None, **kwargs) -> None:
    result = LogRecord(self.name, level, None, 0, msg, args, exc_info, **kwargs)
    self.__records.append(result)

  @property
  def records(self) -> Generator[LogRecord, None, None]:
    yield from self.__records
