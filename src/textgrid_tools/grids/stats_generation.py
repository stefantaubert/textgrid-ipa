import io
import logging
from collections import Counter
from logging import Logger, getLogger
from typing import Dict, List, Optional, Tuple, cast

import numpy as np
import pandas as pd
from matplotlib import collections
from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.ticker import FixedLocator
from textgrid import TextGrid
from textgrid.textgrid import TextGrid
from tqdm import tqdm

from textgrid_tools.globals import ExecutionResult
from textgrid_tools.validation import InvalidGridError

# warn_symbols_general = ["\n", "\r", "\t", "\\", "\"", "[", "]", "(", ")", "|", "_", ";", " "]
# f"{x!r}"[1:-1]
# warn_symbols_ipa = warn_symbols_general + ["/", "'"]
# f"Interval [{interval.minTime}, {interval.maxTime}] ({interval.mark!r} -> {''.join(symbols)!r}) contains at least one of these undesired symbols (incl. space): {warn_symbols_str}")
# Content duration vs silence duration in min and percent


SPACE_DISPL = "␣"
NOT_AVAIL_VAL = "N/A"


def print_stats(grids: List[TextGrid], logger: Optional[Logger]) -> Tuple[ExecutionResult, Optional[Figure], Optional[str]]:
  if logger is None:
    logger = getLogger(__name__)

  for grid in grids:
    if error := InvalidGridError.validate(grid):
      return (error, False), None, None

  durations: List[float] = []
  intervals_durations: Dict[str, List[float]] = {}
  intervals_vocabulary: Dict[str, List[str]] = {}
  for grid in tqdm(grids, desc="Generating statistics", unit=" grid(s)"):
    duration = grid.maxTime - grid.minTime
    durations.append(duration)
    for tier in grid.tiers:
      if tier.name not in intervals_durations:
        intervals_durations[tier.name] = []
      tier_durations = [interval.maxTime - interval.minTime for interval in tier.intervals]
      intervals_durations[tier.name].extend(tier_durations)

      if tier.name not in intervals_vocabulary:
        intervals_vocabulary[tier.name] = []
      vocabulary = [interval.mark for interval in tier.intervals]
      intervals_vocabulary[tier.name].extend(vocabulary)

  total_duration = sum(durations)
  logger.info(
    f"Total duration: {total_duration:.2f}s / {total_duration/60:.2f}min / {total_duration/60/60:.2f}h")

  mark_log = print_mark_stats(intervals_vocabulary)
  fig = get_durations_fig(intervals_durations, durations)

  return (None, False), fig, mark_log


def print_mark_stats(vocabulary: Dict[str, List[str]]) -> str:
  result = ""
  for tier, symbols in vocabulary.items():
    df = get_marks_df(symbols)
    result += f"Tier:;\"{tier}\"\n\n"
    with io.StringIO() as stream:
      df.to_csv(stream, sep=";", index=False)
      result += stream.getvalue()
    result += "\n"
  return result


def get_marks_df(symbols: List[str]) -> pd.DataFrame:
  symbols_counter = Counter(symbols)
  data = []
  for symbol, count in sorted(symbols_counter.items()):
    data.append((repr(symbol)[1:-1], count, count / len(symbols) * 100))
  data.append(("Total", len(symbols), 100))
  result = pd.DataFrame(data, columns=["Mark", "Occurrence", "Occurrence in %"])

  return result


def get_durations_fig(durations: Dict[str, List[float]], grid_durations: List[float]):
  # None for correct display of values
  keys = [None] + list(reversed([f"\"{key}\"" for key in durations.keys()])) + ["Grids"]
  values = list(reversed(list(durations.values()))) + [grid_durations]

  all_values = (val for value in values for val in value)
  maximum = max(all_values)
  maximum = round(maximum, 1) + 0.1

  height_symbol = 0.6
  width_second = 12

  width = width_second * maximum
  height = height_symbol * len(keys)

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
  ax.set_ylabel("Tier")
  ax.set_xlabel("Time in seconds")
  # xticks = np.linspace(0, maximum, num=10)
  xticks = np.arange(0, maximum, 0.05)
  ax.set_xticks(xticks)
  ax.set_xlim(0, maximum)

  xminorticks = np.arange(0, maximum, 0.01)
  ax.xaxis.set_minor_locator(FixedLocator(xminorticks))
  ax.set_title("Distribution of durations")

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

  max_tier_len = max(len(k) for k in keys if k is not None)
  left_padding = (max_tier_len / 1400) + 0.01

  plt.subplots_adjust(
    left=left_padding,  # 0.02,
    right=0.998,
    bottom=0.2,
    # top=0.1,
    # wspace=0.1,
    # hspace=0.2,
  )

  return fig
