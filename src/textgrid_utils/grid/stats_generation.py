import logging
from collections import Counter, OrderedDict
from logging import getLogger
from math import ceil
from typing import Any, Dict, Generator, Iterable, List, Optional
from typing import OrderedDict as OrderedDictType
from typing import Set, Tuple, cast

import matplotlib
import numpy as np
import pandas as pd
from matplotlib import collections
from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.ticker import AutoMinorLocator, FixedLocator, MultipleLocator
from numpy.core.fromnumeric import mean
from ordered_set import OrderedSet
from pandas import DataFrame
from text_utils import StringFormat, Symbol
from textgrid.textgrid import Interval, IntervalTier, TextGrid
from textgrid_utils.globals import ExecutionResult
from textgrid_utils.helper import (get_all_intervals,
                                   get_mark_symbols_intervals)
from textgrid_utils.validation import (InvalidGridError,
                                       NotExistingTierError)

# warn_symbols_general = ["\n", "\r", "\t", "\\", "\"", "[", "]", "(", ")", "|", "_", ";", " "]
# f"{x!r}"[1:-1]
# warn_symbols_ipa = warn_symbols_general + ["/", "'"]
# f"Interval [{interval.minTime}, {interval.maxTime}] ({interval.mark!r} -> {''.join(symbols)!r}) contains at least one of these undesired symbols (incl. space): {warn_symbols_str}")
# Content duration vs silence duration in min and percent


SPACE_DISPL = "␣"
NOT_AVAIL_VAL = "N/A"


def print_stats(grid: TextGrid, duration_threshold: float, text_tier_names: OrderedSet[str], symbols_tier_names: OrderedSet[str]) -> ExecutionResult:
  if error := InvalidGridError.validate(grid):
    return error, False

  for tier_name in symbols_tier_names:
    if error := NotExistingTierError.validate(grid, tier_name):
      return error, False

  logger = getLogger(__name__)
  logger.info(f"Start: {grid.minTime}")
  logger.info(f"End: {grid.maxTime}")
  logger.info(f"Duration: {grid.maxTime - grid.minTime}s")
  logger.info(f"# Tiers: {len(grid.tiers)}")
  for nr, tier in enumerate(cast(Iterable[IntervalTier], grid.tiers), start=1):
    logger.info(f"== Tier {nr} ==")
    string_format = None
    if tier.name in text_tier_names:
      string_format = StringFormat.TEXT
    elif tier.name in symbols_tier_names:
      string_format = StringFormat.SYMBOLS
    print_stats_tier(tier, duration_threshold, string_format)
  return None, False


def print_stats_tier(tier: IntervalTier, duration_threshold: float, string_format: Optional[StringFormat]) -> None:
  logger = getLogger(__name__)
  logger.info(f"Name: {tier.name}")
  logger.info(f"# Intervals: {len(tier.intervals)}")
  if len(tier.intervals) == 0:
    return
  durations = [interval.duration() for interval in cast(List[Interval], tier.intervals)]
  if string_format is not None:
    symbol_stats = get_symbols_statistics(tier.intervals, string_format)

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


def get_symbols_statistics(intervals: List[Interval], string_format: StringFormat):
  interval_symbols = get_mark_symbols_intervals(intervals, string_format)
  interval_symbols = (symbol for symbol in interval_symbols)

  counts = Counter(interval_symbols)
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