from logging import Logger, getLogger
from typing import Optional, Set

from textgrid import TextGrid

from textgrid_tools.globals import ExecutionResult
from textgrid_tools.helper import get_all_intervals, get_mark
from textgrid_tools.validation import InvalidGridError, NotExistingTierError, ValidationError


class NothingDefinedToRemoveError(ValidationError):
  @classmethod
  def validate(cls, symbols: Set[str], marks_symbols: Set[str], marks: Set[str]):
    if len(symbols) == 0 and len(marks_symbols) == 0 and len(marks) == 0:
      return cls()
    return None

  @property
  def default_message(self) -> str:
    return "Anything to remove needs to be set!"


def remove_symbols(grid: TextGrid, tier_names: Set[str], text: Set[str], marks_text: Set[str], marks: Set[str], logger: Optional[Logger]) -> ExecutionResult:
  assert len(tier_names) > 0

  if logger is None:
    logger = getLogger(__name__)

  if error := InvalidGridError.validate(grid):
    return error, False

  for tier_name in tier_names:
    if error := NotExistingTierError.validate(grid, tier_name):
      return error, False

  intervals = list(get_all_intervals(grid, tier_names))

  logger.debug(f"Removing text: {' '.join(sorted(text))}...")
  logger.debug(f"Removing marks: {' '.join(sorted(marks))}...")
  logger.debug(f"Removing marks containing only text: {' '.join(sorted(marks_text))}...")

  changed_anything = False

  for interval in intervals:
    old_mark = get_mark(interval)
    new_mark = get_updated_mark(old_mark, text, marks_text, marks)
    if new_mark != old_mark:
      logger.debug(f"Changed \"{old_mark}\" to \"{new_mark}\".")
      interval.mark = new_mark
      changed_anything = True

  return None, changed_anything


def get_updated_mark(mark: str, text: Set[str], marks_text: Set[str], marks: Set[str]) -> str:
  mark = replace_marks(mark, marks)
  mark = replace_marks_text(mark, marks_text)
  mark = replace_text(mark, text)
  return mark


def replace_marks(mark: str, marks: Set[str]) -> str:
  if mark in marks:
    return ""
  return mark


def replace_marks_text(mark: str, marks_text: Set[str]) -> str:
  tmp = mark
  for repl in marks_text:
    tmp = tmp.replace(repl, "")
  if tmp == "":
    return ""
  return mark


def replace_text(mark: str, text: Set[str]) -> str:
  res = mark
  for repl in text:
    res = res.replace(repl, "")
  return res
