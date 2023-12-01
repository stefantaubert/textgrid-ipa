import io
import logging
import math
from collections import Counter, OrderedDict
from logging import Logger, getLogger
from typing import Dict, List, Optional, Set, Tuple, cast

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


def compare_multiple_grids(grids: List[Tuple[TextGrid, TextGrid]], tier: str, ignore_marks: Set[str], limits_ms_excl: Set[float]) -> pd.DataFrame:
  # TODO add error handling
  all_diffs = {}
  for grid1, grid2 in grids:
    diffs = compare_grids(grid1, grid2, tier, ignore_marks)
    for mark, diff in diffs:
      if mark not in all_diffs:
        all_diffs[mark] = []
      all_diffs[mark].append(diff)
  return get_df_from_diffs(all_diffs, limits_ms_excl)

def get_df_from_diffs(diffs: Dict[str, List[float]], limits_ms_excl: Set[float]) -> pd.DataFrame:
  sorted_marks = sorted(diffs.keys())
  rows = []
  for mark in sorted_marks:
    mark_diffs = diffs[mark]
    row = OrderedDict()
    row["Mark"] = mark
    row["Occurences"] = len(mark_diffs)
    row["MinDiff"] = min(mark_diffs)
    row["MaxDiff"] = max(mark_diffs)
    row["MeanDiff"] = np.mean(mark_diffs)
    row["MedianDiff"] = np.median(mark_diffs)
    row["SumDiff"] = np.sum(mark_diffs)
    if len(limits_ms_excl) > 0:
      extended_limits = [0] + list(sorted((limits_ms_excl - {0, math.inf}))) + [math.inf]
      for i in range(len(extended_limits)-1):
        min_lim = extended_limits[i]
        max_lim = extended_limits[i+1]
        match_limit_count = sum(1 for x in mark_diffs if min_lim <= x < max_lim)
        # TODO make orderer all after each other
        row[f"Match[{min_lim},{max_lim})ms"] = match_limit_count
        row[f"Match[{min_lim},{max_lim})ms%"] = match_limit_count / len(mark_diffs) * 100
    rows.append(row)
  # TODO add total row
  df = pd.DataFrame.from_records(rows)
  return df

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
    diff_s = i1.duration() - i2.duration()
    diff_ms = diff_s * 1000
    diffs.append((i1.mark, abs(diff_ms)))
  
  return diffs