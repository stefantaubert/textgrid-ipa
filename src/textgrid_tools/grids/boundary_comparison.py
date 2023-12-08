import io
import logging
import math
from collections import Counter, OrderedDict
from logging import Logger, getLogger
from typing import Dict, Generator, Iterable, List, Optional, Set, Tuple, cast

import numpy as np
import pandas as pd
from matplotlib import collections
from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.ticker import FixedLocator
from ordered_set import OrderedSet
from scipy.stats import kurtosis
from textgrid import Interval, TextGrid
from textgrid.textgrid import TextGrid
from tqdm import tqdm

from textgrid_tools.globals import ExecutionResult
from textgrid_tools.helper import get_single_tier
from textgrid_tools.validation import InvalidGridError

LATEX_TEXT_WIDTH = 5.90666

def compare_multiple_grids(grids: List[Tuple[TextGrid, TextGrid]], tier: str, ignore_marks: Set[str], limits_ms_excl: Set[float]) -> Tuple[pd.DataFrame, Figure]:
  # TODO add error handling
  all_diffs = {}
  durations1 = {}
  durations2 = {}
  for grid1, grid2 in grids:
    extend_dict(all_diffs,  tuples_to_dict(compare_grids(grid1, grid2, tier, ignore_marks)))
    extend_dict(durations1, tuples_to_dict(get_marks_durations_ms(grid1, tier, ignore_marks)))
    extend_dict(durations2, tuples_to_dict(get_marks_durations_ms(grid2, tier, ignore_marks)))
  
  df = get_df_from_diffs(all_diffs, limits_ms_excl, durations1, durations2)

  logging.getLogger('matplotlib.font_manager').disabled = True
  
  fig, axes = plt.subplots(
    ncols=3,
    nrows=1,
    edgecolor="black",
    linewidth=0,
  )
  axes = cast(List[Axes], axes)
  assert all_diffs.keys() ==durations1.keys()==durations2.keys()
  ax = axes[0]
  plot_violin_diffs(ax, durations1)
  set_xticks(ax, 0, 450, 150,75)
  ax.set_xlabel("Dauer (ms)")
  ax.set_title("Ground Truth")
  
  ax = axes[1]
  plot_violin_diffs(ax, durations2)
  set_xticks(ax, 0, 450, 150,75)
  ax.set_xlabel("Dauer (ms)")
  ax.set_ylabel("")
  ax.set_yticklabels([])
  ax.set_title("Tacotron")
  
  ax = axes[2]
  plot_violin_diffs(ax, all_diffs)
  set_xticks(ax, 0, 200, 50,10)
  ax.set_xlabel("Unterschied (ms)")
  ax.set_ylabel("")
  ax.set_yticklabels([])
  ax.set_title("Vergleich")
  
  plt.gcf().set_size_inches(LATEX_TEXT_WIDTH, 6)

  plt.tight_layout(
    pad=0.2,
  )
  logging.getLogger('matplotlib.font_manager').disabled = False
  
  return df, fig

def tuples_to_dict(tuples: Iterable[Tuple[str, float]]) -> Dict[str, List[float]]:
  result = {}
  for k, val in tuples:
    if k not in result:
      result[k] = []
    result[k].append(val)
  return result

def extend_dict(d: Dict[str, List[float]], d2: Dict[str, List[float]]) -> None:
  for k, v in d2.items():
    if k not in d:
      d[k] = list(v)
    else:
      d[k].extend(v)

def get_df_from_diffs(diffs: Dict[str, List[float]], limits_ms_excl: Set[float], durations1: Dict[str, List[float]],  durations2: Dict[str, List[float]]) -> pd.DataFrame:
  sorted_marks = sorted(diffs.keys())
  rows = []
  
  limits = []
  if len(limits_ms_excl) > 0:
    extended_limits = [-1] + list(sorted((limits_ms_excl - {0, math.inf}))) + [math.inf]
    for i in range(len(extended_limits)-1):
      min_lim = extended_limits[i]
      max_lim = extended_limits[i+1]
      limits.append((min_lim, max_lim))
  
  for mark in sorted_marks:
    mark_diffs = diffs[mark]
    row = OrderedDict()
    row["Mark"] = mark
    row["Occurrences"] = len(mark_diffs)
    row["MeanDurA"] = np.mean(durations1[mark])
    row["MeanDurB"] = np.mean(durations2[mark])
    row["MinDiff"] = min(mark_diffs)
    row["MaxDiff"] = max(mark_diffs)
    row["MeanDiff"] = np.mean(mark_diffs)
    row["MedianDiff"] = np.median(mark_diffs)
    row["SumDiff"] = np.sum(mark_diffs)
    match_limit_counts = [
      sum(1 for x in mark_diffs if min_lim < x <= max_lim)
      for min_lim, max_lim in limits
    ]
    for (min_lim, max_lim), count in zip(limits,match_limit_counts):
      row[f"Match[{min_lim},{max_lim})ms"] = count
      
    for (min_lim, max_lim), count in zip(limits,match_limit_counts):
      row[f"Match[{min_lim},{max_lim})ms%"] = count / len(mark_diffs) * 100
    rows.append(row)
    
  row = OrderedDict()
  row["Mark"] = "-ALL-"
  row["Occurrences"] = np.sum([r["Occurrences"] for r in rows])
  row["MeanDurA"] = np.mean([r["MeanDurA"] for r in rows])
  row["MeanDurB"] =  np.mean([r["MeanDurB"] for r in rows])
  row["MinDiff"] = np.min([r["MinDiff"] for r in rows])
  row["MaxDiff"] = np.max([r["MaxDiff"] for r in rows])
  row["MeanDiff"] = np.mean([r["MeanDiff"] for r in rows])
  row["MedianDiff"] = np.median([r["MedianDiff"] for r in rows])
  row["SumDiff"] = np.sum([r["SumDiff"] for r in rows])
  for min_lim, max_lim in limits:
    row[f"Match[{min_lim},{max_lim})ms"] = np.sum([r[f"Match[{min_lim},{max_lim})ms"] for r in rows])
  for min_lim, max_lim in limits:
    row[f"Match[{min_lim},{max_lim})ms%"] = np.mean([r[f"Match[{min_lim},{max_lim})ms%"] for r in rows])
  all_row = row
  
  row = OrderedDict()
  row["Mark"] = "-ALL (Precise)-"
  row["Occurrences"] = np.sum([r["Occurrences"] for r in rows])
  row["MeanDurA"] = np.mean([x for v in durations1.values() for x in v])
  row["MeanDurB"] =  np.mean([x for v in durations2.values() for x in v])
  row["MinDiff"] = np.min([r["MinDiff"] for r in rows])
  row["MaxDiff"] = np.max([r["MaxDiff"] for r in rows])
  row["MeanDiff"] =  np.mean([x for v in diffs.values() for x in v])
  row["MedianDiff"] = np.median([x for v in diffs.values() for x in v])
  row["SumDiff"] = np.sum([r["SumDiff"] for r in rows])
  for min_lim, max_lim in limits:
    row[f"Match[{min_lim},{max_lim})ms"] = np.sum([r[f"Match[{min_lim},{max_lim})ms"] for r in rows])
  for min_lim, max_lim in limits:
    row[f"Match[{min_lim},{max_lim})ms%"] = row[f"Match[{min_lim},{max_lim})ms"] / row["Occurrences"] * 100
    
  rows.append(all_row)
  rows.append(row)
  
  df = pd.DataFrame.from_records(rows)
  return df

def plot_violin_diffs(ax: Axes, diffs: Dict[str, List[float]]):
  order = list(reversed(sorted(diffs.keys())))
  keys = [None] + list(order)
  values = [diffs[k] for k in order]

  ax.grid(b=True, axis="x", which="major", zorder=1)
  ax.grid(b=True, axis="x", which="minor", zorder=1, alpha=0.5)
  parts = ax.violinplot(
    values, 
    widths=0.9, 
    showmeans=False,
    showmedians=True,
    showextrema=False,
    vert=False,
  )
  
  ax.set_ylabel("Phoneme")
  ax.set_xlabel("Ausrichtungsdifferenz (ms)")
  
  ax.set_yticks(range(len(keys)))
  ax.set_yticklabels(keys)
  ax.set_ylim(0, len(keys))
  
  # all_values = (val for value in values for val in value)
  # maximum = max(all_values)
  # maximum = round(maximum, 0) + 1

  # xticks = np.arange(0, maximum, 20)
  # ax.set_xticks(xticks)
  # ax.set_xlim(0, maximum)

  # xminorticks = np.arange(0, maximum, 10)
  # ax.xaxis.set_minor_locator(FixedLocator(xminorticks))

  # ax.tick_params(axis='y', which='minor', right=False)

  pc: collections.PolyCollection
  for pc in parts['bodies']:
    pc.set_facecolor('white')
    pc.set_edgecolor('black')
    pc.set_alpha(1)
    pc.set_zorder(2)

def set_xticks(ax, tick_min, tick_max, tick_maj, tick_minor):
  xticks = np.arange(tick_min, tick_max + tick_maj, tick_maj)
  ax.set_xticks(xticks)
  ax.set_xlim(tick_min, tick_max)
  xminorticks = np.arange(tick_min, tick_max, tick_minor)
  ax.xaxis.set_minor_locator(FixedLocator(xminorticks))


def plot_violin_durs(ax: Axes, durations: Dict[str, List[float]]):
  order = list(reversed(sorted(durations.keys())))
  keys = [None] + list(order)
  values = [durations[k] for k in order]

  ax.grid(b=True, axis="x", which="major", zorder=1)
  ax.grid(b=True, axis="x", which="minor", zorder=1, alpha=0.5)
  parts = ax.violinplot(
    values, 
    widths=0.9, 
    showmeans=False,
    showmedians=True,
    showextrema=False,
    vert=False,
  )
  
  ax.set_ylabel("Phoneme")
  ax.set_xlabel("Phonemdauer (ms)")
  
  ax.set_yticks(range(len(keys)))
  ax.set_yticklabels(keys)
  ax.set_ylim(0, len(keys))
  
  all_values = (val for value in values for val in value)
  maximum = max(all_values)
  maximum = round(maximum, 0) + 1

  xticks = np.arange(0, maximum, 20)
  ax.set_xticks(xticks)
  ax.set_xlim(0, maximum)

  xminorticks = np.arange(0, maximum, 10)
  ax.xaxis.set_minor_locator(FixedLocator(xminorticks))

  ax.tick_params(axis='y', which='minor', right=False)

  pc: collections.PolyCollection
  for pc in parts['bodies']:
    pc.set_facecolor('white')
    pc.set_edgecolor('black')
    pc.set_alpha(1)
    pc.set_zorder(2)


def get_marks_durations_ms(grid: TextGrid, tier: str,ignore_marks: Set[str]) -> Generator[Tuple[str, float], None, None]:
  tier = get_single_tier(grid, tier)
  for i in tier.intervals:
    if i.mark not in ignore_marks:
      yield (i.mark, i.duration() * 1000) 
  

def compare_grids(grid1: TextGrid, grid2: TextGrid, tier: str, ignore_marks: Set[str]) -> List[Tuple[str, float]]:
  tier1 = get_single_tier(grid1, tier)
  tier2 = get_single_tier(grid2, tier)
  intervals1: List[Interval] = [i for i in tier1.intervals if i.mark not in ignore_marks]
  intervals2: List[Interval] = [i for i in tier2.intervals if i.mark not in ignore_marks]
  if len(intervals1) != len(intervals2):
    raise Exception(f"Not equal interval count: {len(intervals1)} vs. {len(intervals2)}!")
  diffs = []
  for i1, i2 in zip(intervals1, intervals2):
    if i1.mark != i2.mark:
      raise Exception("Mark mismatch!")
    mark = i1.mark
    diff_s = i1.duration() - i2.duration()
    diff_ms = diff_s * 1000
    diff_ms = round(diff_ms)
    diffs.append((mark, abs(diff_ms)))
  
  return diffs