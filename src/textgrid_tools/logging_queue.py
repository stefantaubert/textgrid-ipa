import sys
import warnings
from logging import (CRITICAL, DEBUG, ERROR, INFO, NOTSET, WARNING, Handler, Logger, LogRecord,
                     _srcfile, raiseExceptions)
from typing import Generator, List


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


class StoreRecordsHandler(Handler):
  def __init__(self, level: int = ...) -> None:
    super().__init__(level)
    self.__records = []

  def handle(self, record) -> None:
    self.__records.append(record)

  def emit(self, record: LogRecord) -> None:
    pass

  @property
  def records(self) -> List[LogRecord]:
    return self.__records


class QueuedLogger(Logger):
  """helper class to stack logs for a grid file"""

  def __init__(self, name: str, level=NOTSET) -> None:
    super().__init__(name, level)
    self.__records = []

  def _log(self, level, msg, args, exc_info=None, extra=None, stack_info=False,
           stacklevel=1):
    sinfo = None
    if _srcfile:
      try:
        fn, lno, func, sinfo = self.findCaller(stack_info, stacklevel)
      except ValueError:  # pragma: no cover
        fn, lno, func = "(unknown file)", 0, "(unknown function)"
    else:  # pragma: no cover
      fn, lno, func = "(unknown file)", 0, "(unknown function)"
    if exc_info:
      if isinstance(exc_info, BaseException):
        exc_info = (type(exc_info), exc_info, exc_info.__traceback__)
      elif not isinstance(exc_info, tuple):
        exc_info = sys.exc_info()
    record = self.makeRecord(self.name, level, fn, lno, msg, args,
                             exc_info, func, extra, sinfo)
    self.__records.append(record)

  @property
  def records(self) -> Generator[LogRecord, None, None]:
    yield from self.__records


class QueuedLogger2(Logger):
  pass
