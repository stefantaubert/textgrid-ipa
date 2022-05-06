import logging
import os
from logging import DEBUG, Formatter, Handler, Logger, LogRecord, StreamHandler, getLogger
from logging.handlers import QueueHandler
from pathlib import Path
from queue import Queue
from typing import Dict, Generator, List, Tuple

from ordered_set import OrderedSet

# class StoreRecordsHandler(Handler):
# slower than other impl (maybe due to lock-things)
#   def __init__(self, level: int = DEBUG) -> None:
#     super().__init__(level)
#     self.__records = []

#   def handle(self, record) -> None:
#     self.__records.append(record)

#   def emit(self, record: LogRecord) -> None:
#     pass

#   @property
#   def records(self) -> List[LogRecord]:
#     return self.__records


class StoreRecordsHandler():
  def __init__(self) -> None:
    self.__records = []
    self.level = DEBUG

  def handle(self, record) -> None:
    self.__records.append(record)

  @property
  def records(self) -> List[LogRecord]:
    return self.__records


class ConsoleFormatter(logging.Formatter):
  """Logging colored formatter, adapted from https://stackoverflow.com/a/56944256/3638629"""

  grey = '\x1b[38;21m'
  # blue = '\x1b[38;5;39m'
  yellow = '\x1b[38;5;226m'
  red = '\x1b[1;49;31m'
  bold_red = '\x1b[1;49;31m'
  reset = '\x1b[0m'

  def __init__(self):
    super().__init__()
    self.datefmt = '%H:%M:%S'
    fmt = '(%(levelname)s) %(message)s'
    fmt_info = '%(message)s'

    self.fmts = {
        logging.NOTSET: self.grey + fmt + self.reset,
        logging.DEBUG: self.grey + fmt + self.reset,
        logging.INFO: fmt_info,
        logging.WARNING: self.yellow + fmt + self.reset,
        logging.ERROR: self.red + fmt + self.reset,
        logging.CRITICAL: self.bold_red + fmt + self.reset,
    }

  def format(self, record):
    log_fmt = self.fmts.get(record.levelno)
    formatter = logging.Formatter(log_fmt, self.datefmt)

    return formatter.format(record)


def add_console_out(logger: Logger):
  console = StreamHandler()
  logger.addHandler(console)
  set_console_formatter(console)


def init_and_get_console_logger(name: str) -> Logger:
  logger = getLogger(name)
  logger.parent = get_file_logger()
  logger.handlers.clear()
  assert len(logger.handlers) == 0
  add_console_out(logger)
  return logger


def init_file_stem_loggers(file_stems: OrderedSet[str]) -> Dict[str, Queue]:
  logging_queues = dict.fromkeys(file_stems)
  for k in file_stems:
    logger = getLogger(k)
    logger.propagate = False
    q = Queue(-1)
    logging_queues[k] = q
    handler = QueueHandler(q)
    logger.addHandler(handler)

  return logging_queues


def init_file_stem_logger_lists(file_stems: OrderedSet[str]) -> Dict[str, List[Tuple[int, str]]]:
  logging_queues = dict.fromkeys(file_stems)
  for k in file_stems:
    logging_queues[k] = []
  return logging_queues


def get_file_stem_loggers(file_stems: OrderedSet[str]) -> Generator[Logger, None, None]:
  for k in file_stems:
    logger = getLogger(k)
    yield logger


def write_file_stem_loggers_to_file_logger(queues: Dict[str, Queue]) -> None:
  flogger = get_file_logger()
  for k, q in queues.items():
    flogger.info(f"Log messages for file: {k}")
    entries = list(q.queue)
    for x in entries:
      flogger.handle(x)


def write_file_stem_logger_lists_to_file_logger(lists: Dict[str, List[Tuple[int, str]]]) -> None:
  flogger = get_file_logger()
  for k, l in lists.items():
    flogger.info(f"Log messages for file: {k}")
    for lvl, msg in l:
      flogger.log(lvl, msg)


def set_console_formatter(handler: Handler) -> None:
  logging_formatter = ConsoleFormatter()
  handler.setFormatter(logging_formatter)


def set_logfile_formatter(handler: Handler) -> None:
  fmt = '[%(asctime)s.%(msecs)03d] (%(levelname)s) %(message)s'
  datefmt = '%Y/%m/%d %H:%M:%S'
  logging_formatter = Formatter(fmt, datefmt)
  handler.setFormatter(logging_formatter)


def configure_root_logger() -> None:
  # productive = False
  # loglevel = logging.INFO if productive else logging.DEBUG
  main_logger = getLogger()
  main_logger.setLevel(logging.DEBUG)
  main_logger.manager.disable = logging.NOTSET
  if len(main_logger.handlers) > 0:
    console = main_logger.handlers[0]
  else:
    console = logging.StreamHandler()
    main_logger.addHandler(console)

  set_console_formatter(console)
  console.setLevel(logging.DEBUG)


def get_file_logger() -> Logger:
  logger = getLogger("file-logger")
  if logger.propagate:
    logger.propagate = False
  return logger


def try_init_file_logger(path: Path, debug: bool = False) -> bool:
  if path.is_dir():
    logger = getLogger(__name__)
    logger.error("Logging path is a directory!")
    return False
  flogger = get_file_logger()
  assert len(flogger.handlers) == 0
  try:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file():
      os.remove(path)
    path.write_text("")
    fh = logging.FileHandler(path)
  except Exception as ex:
    logger = getLogger(__name__)
    logger.error("Logfile couldn't be created!")
    logger.exception(ex)
    return False

  set_logfile_formatter(fh)

  level = logging.DEBUG if debug else logging.INFO
  fh.setLevel(level)
  flogger.addHandler(fh)
  return True
