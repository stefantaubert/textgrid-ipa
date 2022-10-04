import math
from logging import Logger, getLogger
from typing import Dict, List, Literal, Optional, Set, Tuple, cast

import numpy as np
from matplotlib.figure import Figure
from textgrid import Interval, IntervalTier, TextGrid

from textgrid_tools.globals import ExecutionResult
from textgrid_tools.helper import get_single_tier
from textgrid_tools.validation import InvalidGridError, NotExistingTierError


def label_durations(grids: Dict[str, List[TextGrid]], tier_name: str, assign_mark: str, scope: Optional[Literal["local", "global"]], only_consider_marks: Optional[Set[str]], range_mode: Literal["percent", "percentile", "absolute"], mode: Literal["together", "content"], range_min: float, range_max: float, logger: Optional[Logger]) -> Tuple[ExecutionResult, Optional[Figure]]:
  assert scope in {"local", "global"}
  assert mode in {"together", "content"}
  assert range_mode in {"percent", "percentile", "absolute"}
  # if range_mode in {"percent", "percentile"}:
  #   assert range_min is not None
  #   assert range_max is not None

  if logger is None:
    logger = getLogger(__name__)

  for speaker_name, speaker_grids in grids.items():
    for grid in speaker_grids:
      if error := InvalidGridError.validate(grid):
        return (error, False), None

      if error := NotExistingTierError.validate(grid, tier_name):
        return (error, False), None

  if range_mode == "absolute":
    return label_durations_core_absolute(grids, tier_name, assign_mark, only_consider_marks, range_min, range_max, logger)

  if scope == "global":
    all_grids = [grid for speaker_grids in grids.values() for grid in speaker_grids]
    return label_durations_core(all_grids, tier_name, assign_mark, only_consider_marks, range_mode, mode, range_min, range_max, logger)

  assert scope == "local"
  changed_anything_all = False
  for speaker_name, speaker_grids in grids.items():
    error, changed_anything = label_durations_core(
      speaker_grids, tier_name, assign_mark, only_consider_marks, range_mode, mode, range_min, range_max, logger)
    if error is not None:
      return error
    changed_anything_all |= changed_anything
  return (None, changed_anything_all)


def label_durations_core_absolute(grids: Dict[str, List[TextGrid]], tier_name: str, assign_mark: str, only_consider_marks: Optional[Set[str]], range_min: float, range_max: float, logger: Logger) -> ExecutionResult:
  changed_intervals = 0
  matching_intervals = 0
  considered_intervals = 0
  for speaker_name, speaker_grids in grids.items():
    for speaker_grid in speaker_grids:
      intervals = get_single_tier(speaker_grid, tier_name).intervals
      for interval in intervals:
        mark = interval.mark
        consider_mark = only_consider_marks is None or mark in only_consider_marks
        if not consider_mark:
          continue
        duration_match = range_min <= interval.duration() < range_max
        if duration_match:
          matching_intervals += 1
          if interval.mark != assign_mark:
            interval.mark = assign_mark
            changed_intervals += 1
      considered_intervals += len(intervals)

  logger.info(f"{matching_intervals} of {considered_intervals} are matching")
  if changed_intervals > 0:
    logger.info(f"Changed {changed_intervals} interval marks.")
  else:
    logger.info("All intervals have the correct mark already assigned.")
  return None, changed_intervals > 0


def label_durations_core(grids: List[TextGrid], tier_name: str, assign_mark: str, only_consider_marks: Optional[Set[str]], range_mode: Literal["percent", "percentile"], mode: Literal["together", "content"], range_min: float, range_max: float, logger: Logger) -> ExecutionResult:
  assert mode in {"together", "content"}
  if mode == "together":
    return label_durations_core_together(grids, tier_name, assign_mark,
                                         only_consider_marks, range_mode, range_min, range_max, logger)
  assert mode == "content"
  return label_durations_core_content(grids, tier_name, assign_mark,
                                      only_consider_marks, range_mode, range_min, range_max, logger)


def label_durations_core_together(grids: List[TextGrid], tier_name: str, assign_mark: str, only_consider_marks: Optional[Set[str]], range_mode: Literal["percent", "percentile"], range_min: float, range_max: float, logger: Logger) -> ExecutionResult:
  assert range_mode in {"percent", "percentile"}

  consider_intervals: List[Interval] = []

  total_intervals = 0
  for grid in grids:
    intervals = get_single_tier(grid, tier_name).intervals
    for interval in intervals:
      mark = interval.mark
      consider_mark = only_consider_marks is None or mark in only_consider_marks
      if not consider_mark:
        continue
      consider_intervals.append(interval)
    total_intervals += len(intervals)
  considered_intervals = len(consider_intervals)

  logger.info(f"{considered_intervals} of {total_intervals} intervals are considered.")

  all_interval_durations = np.array(list(
    interval.duration()
    for interval in consider_intervals
  ))

  if range_mode == "percent":
    max_duration = np.max(all_interval_durations, axis=0)
    min_val = max_duration / 100 * range_min
    if math.isinf(range_max):
      max_val = math.inf
    else:
      max_val = max_duration / 100 * range_max
  elif range_mode == "quantile":
    min_val = np.quantile(all_interval_durations, range_min, axis=0)
    if math.isinf(range_max):
      max_val = math.inf
    else:
      max_val = np.quantile(all_interval_durations, range_max, axis=0)
  else:
    assert False

  changed_intervals = 0
  matching_intervals = 0
  for interval in consider_intervals:
    duration_match = min_val <= interval.duration() < max_val
    if duration_match:
      matching_intervals += 1
      if interval.mark != assign_mark:
        interval.mark = assign_mark
        changed_intervals += 1

  logger.info(f"{matching_intervals} of {considered_intervals} are matching")
  if changed_intervals > 0:
    logger.info(f"Changed {changed_intervals} interval marks.")
  else:
    logger.info("All intervals have the correct mark already assigned.")
  return None, changed_intervals > 0


def label_durations_core_content(grids: List[TextGrid], tier_name: str, assign_mark: str, only_consider_marks: Optional[Set[str]], range_mode: Literal["percent", "percentile"], range_min: float, range_max: float, logger: Logger) -> ExecutionResult:
  assert range_mode in {"percent", "percentile"}

  intervals_to_marks: Dict[str, List[Interval]] = {}

  total_intervals = 0
  considered_intervals = 0
  for grid in grids:
    intervals = get_single_tier(grid, tier_name).intervals
    for interval in intervals:
      mark = interval.mark
      consider_mark = only_consider_marks is None or mark in only_consider_marks
      if not consider_mark:
        continue
      considered_intervals += 1

      if mark not in intervals_to_marks:
        intervals_to_marks[mark] = []
      intervals_to_marks[mark].append(interval)
    total_intervals += len(intervals)

  logger.info(f"{considered_intervals} of {total_intervals} intervals are considered.")

  changed_intervals = 0
  matching_intervals = 0

  for mark, mark_intervals in intervals_to_marks.items():
    all_interval_durations = np.array(list(
      interval.duration()
      for interval in mark_intervals
    ))

    if range_mode == "percent":
      max_duration = np.max(all_interval_durations, axis=0)
      min_val = max_duration / 100 * range_min
      if math.isinf(range_max):
        max_val = math.inf
      else:
        max_val = max_duration / 100 * range_max
    elif range_mode == "quantile":
      min_val = np.quantile(all_interval_durations, range_min, axis=0)
      if math.isinf(range_max):
        max_val = math.inf
      else:
        max_val = np.quantile(all_interval_durations, range_max, axis=0)
    else:
      assert False

    for interval in mark_intervals:
      duration_match = min_val <= interval.duration() < max_val
      if duration_match:
        matching_intervals += 1
        if interval.mark != assign_mark:
          interval.mark = assign_mark
          changed_intervals += 1

  logger.info(f"{matching_intervals} of {considered_intervals} are matching")
  if changed_intervals > 0:
    logger.info(f"Changed {changed_intervals} interval marks.")
  else:
    logger.info("All intervals have the correct mark already assigned.")
  return None, changed_intervals > 0
