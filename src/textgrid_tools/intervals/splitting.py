from logging import Logger, getLogger
from typing import Generator, Iterable, Optional, Set, cast

from textgrid.textgrid import Interval, TextGrid

from textgrid_tools.comparison import check_intervals_are_equal
from textgrid_tools.globals import ExecutionResult
from textgrid_tools.helper import (get_all_tiers, get_mark, interval_is_None_or_empty,
                                   set_intervals_consecutive)
from textgrid_tools.validation import InvalidGridError, NotExistingTierError


def split_intervals(grid: TextGrid, tier_names: Set[str], symbol: str, keep: bool, logger: Optional[Logger]) -> ExecutionResult:
  assert len(tier_names) > 0

  if logger is None:
    logger = getLogger(__name__)

  if error := InvalidGridError.validate(grid):
    return error, False

  for tier_name in tier_names:
    if error := NotExistingTierError.validate(grid, tier_name):
      return error, False

  tiers = list(get_all_tiers(grid, tier_names))

  changed_anything = False

  # for tier in tiers:
  #   intervals_copy = cast(Iterable[Interval], list(tier.intervals))
  #   for interval in intervals_copy:
  #     splitted_intervals = list(get_split_intervals_v2(
  #       interval, symbol, keep))

  #     if not check_intervals_are_equal([interval], splitted_intervals):
  #       replace_intervals(tier, [interval], splitted_intervals)
  #       changed_anything = True

  for tier in tiers:
    intervals_copy = cast(Iterable[Interval], list(tier.intervals))
    new_intervals = list(
      splitted_interval
      for interval in intervals_copy
      for splitted_interval in get_split_intervals(interval, symbol, keep)
    )
    if not check_intervals_are_equal(tier.intervals, new_intervals):
      tier.intervals = new_intervals
      changed_anything = True

  return None, changed_anything


def get_split_intervals(interval: Interval, symbol: str, keep: bool) -> Generator[Interval, None, None]:
  if interval_is_None_or_empty(interval):
    yield interval
  else:
    mark = get_mark(interval)

    if symbol == "":
      parts = list(mark)
    else:
      parts = mark.split(symbol)

    if len(parts) == 1:
      yield interval
    else:
      new_intervals = []
      for part in parts[:-1]:
        new_intervals.append(Interval(0, 1, part))
        if keep:
          new_intervals.append(Interval(0, 1, symbol))
      new_intervals.append(Interval(0, 1, parts[-1]))

      set_intervals_consecutive(new_intervals, interval.minTime, interval.maxTime)

      yield from new_intervals
