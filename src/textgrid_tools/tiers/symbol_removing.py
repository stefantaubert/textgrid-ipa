from logging import getLogger
from typing import Set

from text_utils import Symbols
from text_utils.string_format import StringFormat
from text_utils.types import Symbol
from text_utils.utils import symbols_ignore
from textgrid.textgrid import TextGrid
from textgrid_tools.globals import ExecutionResult
from textgrid_tools.helper import get_all_intervals, get_mark
from textgrid_tools.validation import (InvalidGridError,
                                       InvalidStringFormatIntervalError,
                                       NotExistingTierError,
                                       ValidationError)


class NothingDefinedToRemoveError(ValidationError):
  @classmethod
  def validate(cls, symbols: Set[Symbol], marks_symbols: Set[Symbol], marks: Set[str]):
    if len(symbols) == 0 and len(marks_symbols) == 0 and len(marks) == 0:
      return cls()
    return None

  @property
  def default_message(self) -> str:
    return "Anything to remove needs to be set!"


def remove_symbols(grid: TextGrid, tier_names: Set[str], tiers_string_format: StringFormat, symbols: Set[Symbol], marks_symbols: Set[Symbol], marks: Set[str]) -> ExecutionResult:
  assert len(tier_names) > 0

  if error := InvalidGridError.validate(grid):
    return error, False

  for tier_name in tier_names:
    if error := NotExistingTierError.validate(grid, tier_name):
      return error, False

  intervals = list(get_all_intervals(grid, tier_names))

  if error := InvalidStringFormatIntervalError.validate_intervals(intervals, tiers_string_format):
    return error, False

  logger = getLogger(__name__)
  logger.debug(f"Removing symbols: {' '.join(sorted(symbols))}...")
  logger.debug(f"Removing marks: {' '.join(sorted(marks))}...")
  logger.debug(f"Removing marks_symbols: {' '.join(sorted(marks_symbols))}...")

  changed_anything = False

  for interval in intervals:
    mark = get_mark(interval)
    mark = get_updated_mark(mark, tiers_string_format, symbols, marks_symbols, marks)
    if interval.mark != mark:
      logger.debug(f"Changed \"{interval.mark}\" to \"{mark}\".")
      interval.mark = mark
      changed_anything = True

  return None, changed_anything


def get_updated_mark(mark: str, tiers_string_format: StringFormat, symbols: Set[Symbol], marks_symbols: Set[Symbol], marks: Set[str]) -> str:
  mark = replace_marks(mark, marks)
  interval_symbols = tiers_string_format.convert_string_to_symbols(mark)
  interval_symbols = replace_only_symbols(interval_symbols, marks_symbols)
  interval_symbols = symbols_ignore(interval_symbols, symbols)
  mark = tiers_string_format.convert_symbols_to_string(interval_symbols)
  return mark


def replace_marks(mark: str, marks: Set[str]) -> str:
  if mark in marks:
    return ""
  return mark


def replace_only_symbols(mark_symbols: Symbols, only_symbols: Set[Symbol]) -> Symbols:
  tmp_symbols = symbols_ignore(mark_symbols, only_symbols)
  mark_contains_only_marks_symbols = len(tmp_symbols) == 0
  if mark_contains_only_marks_symbols:
    return tuple()
  return mark_symbols


# def remove_intervals_with_marks(intervals: Iterable[Interval], ignore_marks: Set[str]) -> Generator[Interval, None, None]:
#   result = (
#     interval
#     for interval in intervals
#     if get_mark(interval) not in ignore_marks
#   )
#   return result


# def remove_intervals_with_only_symbols(intervals: Iterable[Interval], only_symbols: Set[str], string_format: StringFormat) -> Generator[Interval, None, None]:
#   result = (
#     interval
#     for interval in intervals
#     if len(symbols_ignore(get_mark_symbols(interval, string_format), only_symbols)) > 0
#   )
#   return result
