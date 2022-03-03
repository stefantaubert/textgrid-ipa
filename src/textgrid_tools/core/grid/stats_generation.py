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
from textgrid_tools.core.globals import ExecutionResult
from textgrid_tools.core.helper import (get_all_intervals,
                                        get_mark_symbols_intervals)
from textgrid_tools.core.validation import (InvalidGridError,
                                            NotExistingTierError)

# warn_symbols_general = ["\n", "\r", "\t", "\\", "\"", "[", "]", "(", ")", "|", "_", ";", " "]
# f"{x!r}"[1:-1]
# warn_symbols_ipa = warn_symbols_general + ["/", "'"]
# f"Interval [{interval.minTime}, {interval.maxTime}] ({interval.mark!r} -> {''.join(symbols)!r}) contains at least one of these undesired symbols (incl. space): {warn_symbols_str}")
# Content duration vs silence duration in min and percent


SPACE_DISPL = "␣"
NOT_AVAIL_VAL = "N/A"


def get_plot_mark_name(mark: str) -> str:
  if mark == "":
    return "EMPTY"
  mark = mark.replace(" ", SPACE_DISPL)
  return mark


def plot_interval_durations_diagram(grid: TextGrid, tier_names: Set[str]) -> Tuple[ExecutionResult, Optional[Figure]]:
  if error := InvalidGridError.validate(grid):
    return (error, False), None

  for tier_name in tier_names:
    if error := NotExistingTierError.validate(grid, tier_name):
      return (error, False), None

  intervals = get_all_intervals(grid, tier_names)
  durations_to_marks: Dict[str, List[float]] = {}
  for interval in intervals:
    mark = interval.mark
    duration = interval.duration()
    if mark not in durations_to_marks:
      durations_to_marks[mark] = []
    durations_to_marks[mark].append(duration)

  durations_to_marks = OrderedDict((
    (key, sorted(durations_to_marks[key]))
    for key in reversed(sorted(durations_to_marks.keys()))
  ))

  keys = [None] + [get_plot_mark_name(key) for key in durations_to_marks.keys()]
  values = list(durations_to_marks.values())

  all_values = (val for value in values for val in value)
  maximum = max(all_values)
  maximum = round(maximum, 1) + 0.1

  height_symbol = 0.2
  width_second = 3

  width = width_second * maximum
  height = height_symbol * len(durations_to_marks)

  logging.getLogger('matplotlib.font_manager').disabled = True

  fig = cast(Figure, plt.figure(figsize=(width, height)))
  ax = cast(Axes, fig.gca())

  ax.grid(b=True, axis="both", which="major", zorder=1)
  ax.grid(b=True, axis="x", which="minor", zorder=1, alpha=0.2)
  # ax.minorticks_on()

  # , widths=0.9, showmeans=False, showmedians=False, showextrema=False)
  parts = ax.violinplot(values, widths=0.9, showmeans=False, showmedians=True,
                        showextrema=False, vert=False)
  ax.set_yticks(range(len(keys)))
  ax.set_yticklabels(keys)
  ax.set_ylim(0, len(keys))
  ax.set_ylabel("Mark")
  ax.set_xlabel("Time in seconds")
  # xticks = np.linspace(0, maximum, num=10)
  xticks = np.arange(0, maximum, 0.1)
  ax.set_xticks(xticks)
  ax.set_xlim(0, maximum)

  xminorticks = np.arange(0, maximum, 0.05)
  ax.xaxis.set_minor_locator(FixedLocator(xminorticks))
  ax.set_title("Distribution of interval durations")

  # disable minor x ticks
  ax.tick_params(axis='y', which='minor', right=False)

  # ax.set_zorder(4)
  pc: collections.PolyCollection
  for pc in parts['bodies']:
    pc.set_facecolor('white')
    pc.set_edgecolor('black')
    pc.set_alpha(1)
    pc.set_zorder(2)
  fig.tight_layout()
  logging.getLogger('matplotlib.font_manager').disabled = False

  padding_h = 0.055
  padding_v = 0.1
  legend_x = 0.1

  # plt.subplots_adjust(
  #   left=padding_h,
  #   bottom=padding_v + legend_x,
  #   right=1 - padding_h,
  #   top=1 - padding_v,
  #   wspace=0.1,
  #   # hspace=0.2,
  # )

  return (None, False), fig


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
  symbols = (symbol for symbol in interval_symbols)

  counts = Counter(symbols)
  all_symbols = OrderedSet(sorted(counts.keys()))

  total_symbol_count = sum(counts.values())

  result: List[OrderedDictType[str, Any]] = []
  for symbol in all_symbols:
    symbol_repr = repr(symbol)[1:-1] if symbol != " " else SPACE_DISPL
    row = {
      "Symbol": symbol_repr,
    }

    symbol_count_total = counts[symbol]
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
