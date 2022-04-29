from logging import getLogger
from typing import Dict, Optional, Set

from textgrid.textgrid import TextGrid

from textgrid_utils.globals import ExecutionResult
from textgrid_utils.helper import get_all_intervals, get_mark
from textgrid_utils.validation import InvalidGridError, NotExistingTierError


def map_marks(grid: TextGrid, mapping: Dict[str, str], tier_names: Set[str], replace_unmapped: bool, replace_unmapped_with: Optional[str], ignore: Set[str]) -> ExecutionResult:
  assert len(tier_names) > 0

  if error := InvalidGridError.validate(grid):
    return error, False

  for tier_name in tier_names:
    if error := NotExistingTierError.validate(grid, tier_name):
      return error, False

  intervals = list(get_all_intervals(grid, tier_names))

  logger = getLogger(__name__)

  changed_anything = False

  for interval in intervals:
    mark = get_mark(interval)
    mapped_mark = map_mark(mark, mapping, ignore, replace_unmapped, replace_unmapped_with)

    if mark != mapped_mark:
      logger.debug(f"Mapped \"{mark}\" to \"{mapped_mark}\".")
      interval.mark = mapped_mark
      changed_anything = True

  return None, changed_anything


def map_mark(mark: str, mapping: Dict[str, str], ignore: Set[str], replace_unknown: bool, replace_unknown_with: Optional[str]) -> str:
  assert isinstance(mark, str)
  if mark in ignore:
    return mark
  has_mapping = mark in mapping
  if has_mapping:
    return mapping[mark]
  if replace_unknown:
    if replace_unknown_with is None or replace_unknown_with == "":
      return ""
    return replace_unknown_with
  return mark
