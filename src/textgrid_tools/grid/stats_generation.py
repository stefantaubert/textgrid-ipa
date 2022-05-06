from collections import Counter
from logging import Logger, getLogger
from typing import Any, Iterable, List, Optional
from typing import OrderedDict as OrderedDictType
from typing import cast

import pandas as pd
from numpy.core.fromnumeric import mean
from ordered_set import OrderedSet
from pandas import DataFrame
from textgrid.textgrid import Interval, IntervalTier, TextGrid

from textgrid_tools.globals import ExecutionResult
from textgrid_tools.helper import get_mark
from textgrid_tools.validation import InvalidGridError

# warn_symbols_general = ["\n", "\r", "\t", "\\", "\"", "[", "]", "(", ")", "|", "_", ";", " "]
# f"{x!r}"[1:-1]
# warn_symbols_ipa = warn_symbols_general + ["/", "'"]
# f"Interval [{interval.minTime}, {interval.maxTime}] ({interval.mark!r} -> {''.join(symbols)!r}) contains at least one of these undesired symbols (incl. space): {warn_symbols_str}")
# Content duration vs silence duration in min and percent


SPACE_DISPL = "␣"
NOT_AVAIL_VAL = "N/A"


def print_stats(grid: TextGrid, duration_threshold: float, logger: Optional[Logger]) -> ExecutionResult:
  if logger is None:
    logger = getLogger(__name__)

  if error := InvalidGridError.validate(grid):
    return error, False

  logger.info(f"Start: {grid.minTime}")
  logger.info(f"End: {grid.maxTime}")
  logger.info(f"Duration: {grid.maxTime - grid.minTime}s")
  logger.info(f"# Tiers: {len(grid.tiers)}")
  for nr, tier in enumerate(cast(Iterable[IntervalTier], grid.tiers), start=1):
    logger.info(f"== Tier {nr} ==")
    print_stats_tier(tier, duration_threshold, logger)
  return None, False


def print_stats_tier(tier: IntervalTier, duration_threshold: float, logger: Logger) -> None:
  logger.info(f"Name: {tier.name}")
  logger.info(f"# Intervals: {len(tier.intervals)}")
  if len(tier.intervals) == 0:
    return
  durations = [interval.duration() for interval in cast(List[Interval], tier.intervals)]
  symbol_stats = get_symbols_statistics(tier.intervals)

  with pd.option_context(
      'display.max_rows', None,
      'display.max_columns', None,
      'display.precision', 7,
      'display.width', None,
    ):
    print(symbol_stats)

  logger.info(f"Min duration: {min(durations)}s")
  logger.info(f"Max duration: {max(durations)}s")
  logger.info(f"Average duration: {mean(durations)}s")

  for interval in cast(Iterable[Interval], tier.intervals):
    if interval.duration() < duration_threshold:
      logger.info(
        f"Very short interval: [{interval.minTime}, {interval.maxTime}] \"{interval.mark}\" -> {interval.duration()}s")


def get_symbols_statistics(intervals: List[Interval]):
  marks = (get_mark(interval) for interval in intervals)

  counts = Counter(marks)
  sorted_counts = counts.most_common()
  sorted_counts.sort(key=lambda kv: kv[1], reverse=True)
  sorted_keys = (key for key, _ in sorted_counts)
  all_interval_symbols = OrderedSet(sorted_keys)

  total_symbol_count = sum(counts.values())

  result: List[OrderedDictType[str, Any]] = []
  for symbols in all_interval_symbols:
    # TODO include (,) as EMPTY
    symbols_reprs = (
      repr(symbol)[1:-1] if symbols != " " else SPACE_DISPL
      for symbol in symbols
    )

    symbol_repr = ' '.join(symbols_reprs)
    row = {
      "Symbol": symbol_repr,
    }

    symbol_count_total = counts[symbols]
    row["Count"] = symbol_count_total

    val = NOT_AVAIL_VAL if total_symbol_count == 0 else symbol_count_total / total_symbol_count * 100
    row["Rel %"] = val
    result.append(row)

  if len(result) > 0:
    cols = result[0].keys()
    rows = (list(row.values()) for row in result)
    df = DataFrame(rows, columns=cols)
    return df
  else:
    return DataFrame()
