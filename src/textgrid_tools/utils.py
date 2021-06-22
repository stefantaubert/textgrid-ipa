from dataclasses import astuple
import pandas as pd
import os
import re
from logging import Logger
from pathlib import Path
from typing import Any, List, Optional, Tuple

from textgrid.textgrid import Interval, IntervalTier, TextGrid


def get_parent_dirpath(filepath: str) -> str:
  return Path(filepath).parent


def durations_to_interval_tier(durations: List[Tuple[str, float]], maxTime: float, name: str) -> IntervalTier:
  intervals = durations_to_intervals(durations, maxTime)
  res = intervals_to_tier(intervals, name)
  return res


def save_dataclasses(items: List[Any], file_path: str):
  data = [astuple(xi) for xi in items]
  dataframe = pd.DataFrame(data)
  dataframe.to_csv(file_path, header=None, index=None, sep="\t")


def intervals_to_tier(intervals: List[Interval], name: str) -> IntervalTier:
  min_time = intervals[0].minTime if len(intervals) > 0 else 0
  max_time = intervals[-1].maxTime if len(intervals) > 0 else 0
  word_tier = IntervalTier(
    minTime=min_time,
    maxTime=max_time,
    name=name,
  )

  word_tier.intervals.extend(intervals)

  return word_tier


def durations_to_intervals(durations: List[Tuple[str, float]], maxTime: float) -> List[Interval]:
  res = []
  start = 0
  for i, word_duration in enumerate(durations):
    word, duration = word_duration
    end = start + duration
    is_last = i == len(durations) - 1
    if is_last:
      # to prevent calculation inprecisions due to float, and therefore an invalid tier size.
      end = maxTime
    word_interval = Interval(
      minTime=start,
      maxTime=end,
      mark=word,
    )
    # word_intervals.append(word_interval)
    res.append(word_interval)
    start = end

  return res


def ms_to_samples(ms, sampling_rate: int):
  res = int(ms * sampling_rate / 1000)
  return res


def check_interval_has_content(interval: Interval) -> bool:
  content = interval.mark.strip()
  has_content = content != ""
  return has_content


def check_paths_ok(in_path: str, out_path: str, logger: Logger) -> bool:
  if not os.path.exists(in_path):
    logger.error("The file couldn't be found!")
    return False

  if in_path == out_path:
    logger.error("Input and output files should be different!")
    return False

  return True


# Regular expression matching whitespace:
_whitespace_re = re.compile(r'\s+')


def collapse_whitespace(text: str) -> str:
  return re.sub(_whitespace_re, ' ', text)


def update_or_add_tier(grid: TextGrid, tier: IntervalTier) -> None:
  if grid_contains_tier(grid, tier.name):
    update_tier(grid, tier)
  else:
    grid.append(tier)


def update_tier(grid: TextGrid, tier: IntervalTier) -> None:
  assert grid_contains_tier(grid, tier.name)
  existing_tier = grid.getFirst(tier.name)
  assert tier.name == existing_tier.name
  existing_tier.intervals.clear()
  existing_tier.intervals.extend(tier.intervals)
  existing_tier.maxTime = tier.maxTime
  existing_tier.minTime = tier.minTime


def grid_contains_tier(grid: TextGrid, tier_name: str) -> bool:
  existing_tier: Optional[IntervalTier] = grid.getFirst(tier_name)
  res = existing_tier is not None
  return res
