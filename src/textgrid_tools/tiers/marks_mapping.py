from logging import Logger, getLogger
from typing import Dict, Iterable, Optional, Set

from textgrid import TextGrid

from textgrid_tools.globals import ExecutionResult
from textgrid_tools.helper import get_all_intervals, get_mark
from textgrid_tools.validation import InvalidGridError, NotExistingTierError


def map_marks(grid: TextGrid, mapping: Dict[str, str], tier_names: Set[str], replace_unmapped: bool, replace_unmapped_with: Optional[str], ignore: Set[str], logger: Optional[Logger]) -> ExecutionResult:
  assert len(tier_names) > 0

  if logger is None:
    logger = getLogger(__name__)

  if error := InvalidGridError.validate(grid):
    return error, False

  for tier_name in tier_names:
    if error := NotExistingTierError.validate(grid, tier_name):
      return error, False

  intervals = list(get_all_intervals(grid, tier_names))

  changed_anything = False

  not_replaced_marks = set()
  replaced_marks = set()
  mapped_count = 0
  for interval in intervals:
    mark = get_mark(interval)
    mapped_mark = map_mark(mark, mapping, ignore, replace_unmapped, replace_unmapped_with)

    if mark != mapped_mark:
      mapped_count += 1
      replaced_marks.add(mark)
      #logger.debug(f"Mapped \"{mark}\" to \"{mapped_mark}\".")
      interval.mark = mapped_mark
      changed_anything = True
    else:
      not_replaced_marks.add(mark)

  logger.info(f"Replaced these marks: {get_printable(replaced_marks)}")
  not_occurred = set(mapping.keys()).difference(replaced_marks)
  logger.info(f"Marks in mapping that didn't occurred: {get_printable(not_occurred)}")

  if len(not_replaced_marks) == 0:
    logger.info("All marks from all intervals were mapped.")
  else:
    logger.info(
      f"Mapped {mapped_count} interval mark(s) of {len(intervals)} total interval(s) in {len(tier_names)} tier(s).")
    logger.info(f"Didn't replaced these marks: {get_printable(not_replaced_marks)}")
  return None, changed_anything


def get_printable(marks: Iterable[str]) -> str:
  content = list(
    f"\"{mark}\"" for mark in sorted(marks)
  )
  result = f"{', '.join(content)} (#{len(content)})"
  return result


def map_mark(mark: str, mapping: Dict[str, str], ignore: Set[str], replace_unmapped: bool, replace_unmapped_with: Optional[str]) -> str:
  assert isinstance(mark, str)
  if mark in ignore:
    return mark
  has_mapping = mark in mapping
  if has_mapping:
    return mapping[mark]
  if replace_unmapped:
    if replace_unmapped_with is None or replace_unmapped_with == "":
      return ""
    return replace_unmapped_with
  return mark
