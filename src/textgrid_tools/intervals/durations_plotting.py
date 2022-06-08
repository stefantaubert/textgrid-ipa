import logging
from collections import OrderedDict
from logging import Logger, getLogger
from typing import Dict, List, Optional, Set, Tuple, cast

import numpy as np
from matplotlib import collections
from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.ticker import FixedLocator
from textgrid import TextGrid

from textgrid_tools.globals import ExecutionResult
from textgrid_tools.helper import get_all_intervals
from textgrid_tools.validation import InvalidGridError, NotExistingTierError

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


def plot_interval_durations_diagram(grid: TextGrid, tier_names: Set[str], logger: Optional[Logger]) -> Tuple[ExecutionResult, Optional[Figure]]:
  if logger is None:
    logger = getLogger(__name__)

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
