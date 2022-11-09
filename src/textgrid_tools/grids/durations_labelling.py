import math
from logging import Logger, getLogger
from typing import Dict, Generator, Iterable, List, Literal, Optional, Set, Tuple

import numpy as np
from textgrid import Interval, TextGrid

from textgrid_tools.globals import ChangedAnything
from textgrid_tools.helper import (get_boundary_timepoints_from_tier, get_interval_on_tier,
                                   get_single_tier)
from textgrid_tools.validation import (BoundaryError, InvalidGridError, NotExistingTierError,
                                       ValidationError)


def label_durations(grids: Dict[str, List[TextGrid]], tier_name: str, assign_tier_name: str, assign_mark: str, scope: Optional[Literal["file", "folder", "all"]], only_consider_marks: Set[str], range_mode: Literal["percent", "percentile", "absolute"], marks_mode: Literal["separate", "all"], range_min: float, range_max: float, min_count: int, logger: Optional[Logger]) -> Tuple[Optional[ValidationError], Dict[str, List[ChangedAnything]]]:
  if logger is None:
    logger = getLogger(__name__)

  for speaker_name, speaker_grids in grids.items():
    for grid in speaker_grids:
      if error := InvalidGridError.validate(grid):
        return error, False

      if error := NotExistingTierError.validate(grid, tier_name):
        return error, False

      if tier_name != assign_tier_name:
        if error := NotExistingTierError.validate(grid, assign_tier_name):
          return error, False

        boundary_tier = get_single_tier(grid, assign_tier_name)
        boundary_tier_timepoints = get_boundary_timepoints_from_tier(boundary_tier)
        tier = get_single_tier(grid, tier_name)
        tier_timepoints = get_boundary_timepoints_from_tier(tier)

        if error := BoundaryError.validate(boundary_tier_timepoints, [tier]):
          return error, False

        if error := BoundaryError.validate(tier_timepoints, [boundary_tier]):
          return error, False

  grids_c = {}
  total_intervals_sum = 0
  considered_intervals_sum = 0
  duration_matching_intervals_sum = 0
  changed_intervals_sum = 0
  count_matching_intervals_sum = 0

  if range_mode == "absolute":
    all_grids = [grid for speaker_name, speaker_grids in grids.items() for grid in speaker_grids]
    changes, total_intervals, considered_intervals, duration_matching_intervals, changed_intervals = label_durations_core_absolute(
      grids, tier_name, assign_tier_name, assign_mark, only_consider_marks, range_min, range_max)

    considered_intervals_sum += considered_intervals
    total_intervals_sum += total_intervals
    count_matching_intervals_sum += total_intervals
    duration_matching_intervals_sum += duration_matching_intervals
    changed_intervals_sum += changed_intervals

    grids_changes = list(
      (speaker_name, changes.pop(0)) for speaker_name, speaker_grids in grids.items() for grid in speaker_grids
    )
    assert len(changes) == 0
    for speaker_name, change in grids_changes:
      if speaker_name not in grids_c:
        grids_c[speaker_name] = []
      grids_c[speaker_name].append(change)
  else:
    if scope == "all":
      all_grids = [grid for speaker_name, speaker_grids in grids.items() for grid in speaker_grids]
      changes, total_intervals, considered_intervals, count_matching_intervals, duration_matching_intervals, changed_intervals = label_durations_core(
        all_grids, tier_name, assign_tier_name, assign_mark, only_consider_marks, range_mode, marks_mode, range_min, range_max, min_count)
      assert len(changes) == len(all_grids)
      considered_intervals_sum += considered_intervals
      total_intervals_sum += total_intervals
      count_matching_intervals_sum += count_matching_intervals
      duration_matching_intervals_sum += duration_matching_intervals
      changed_intervals_sum += changed_intervals

      grids_changes = list(
        (speaker_name, changes.pop(0)) for speaker_name, speaker_grids in grids.items() for grid in speaker_grids
      )
      assert len(changes) == 0

      for speaker_name, change in grids_changes:
        if speaker_name not in grids_c:
          grids_c[speaker_name] = []
        grids_c[speaker_name].append(change)
    elif scope == "folder":
      for speaker_name, speaker_grids in grids.items():
        changes, total_intervals, considered_intervals, count_matching_intervals, duration_matching_intervals, changed_intervals = label_durations_core(speaker_grids, tier_name, assign_tier_name, assign_mark,
                                                                                                                                                        only_consider_marks, range_mode, marks_mode, range_min, range_max, min_count)
        considered_intervals_sum += considered_intervals
        total_intervals_sum += total_intervals
        count_matching_intervals_sum += count_matching_intervals
        duration_matching_intervals_sum += duration_matching_intervals
        changed_intervals_sum += changed_intervals
        grids_c[speaker_name] = changes
    elif scope == "file":
      for speaker_name, speaker_grids in grids.items():
        grids_c[speaker_name] = []
        for grid in speaker_grids:
          changes, total_intervals, considered_intervals, count_matching_intervals, duration_matching_intervals, changed_intervals = label_durations_core_separate(
            [grid], tier_name, assign_tier_name, assign_mark, only_consider_marks, range_mode, range_min, range_max, min_count)
          grids_c[speaker_name].append(changes[0])
          considered_intervals_sum += considered_intervals
          total_intervals_sum += total_intervals
          count_matching_intervals_sum += count_matching_intervals
          duration_matching_intervals_sum += duration_matching_intervals
          changed_intervals_sum += changed_intervals
          grids_c[speaker_name] = changes
    else:
      assert False
      raise NotImplementedError()

  logger.info(
    f"{considered_intervals_sum} of {total_intervals_sum} intervals are considered (due to mark restrictions).")
  if range_mode != "absolute":
    logger.info(
      f"{count_matching_intervals_sum} of {considered_intervals_sum} intervals are considered (due to count restriction)")
  logger.info(
    f"{duration_matching_intervals_sum} of {count_matching_intervals_sum} intervals are matching (due to duration restriction)")
  if changed_intervals > 0:
    logger.info(f"Changed {changed_intervals_sum} interval marks.")
  else:
    logger.info("All intervals have the correct mark already assigned.")
  return None, grids_c


def label_durations_core_absolute(grids: List[TextGrid], tier_name: str, assign_tier_name: str, assign_mark: str, only_consider_marks: Set[str], range_min: float, range_max: float) -> Tuple[List[ChangedAnything], int, int, int]:
  grids_changed = []
  changed_intervals = 0
  matching_intervals = 0
  considered_intervals = 0
  total_intervals = 0
  for speaker_grid in grids:
    changed_anything = False
    tier = get_single_tier(speaker_grid, tier_name)
    intervals = tier.intervals
    total_intervals += len(intervals)
    assign_tier = get_single_tier(speaker_grid, assign_tier_name)
    intervals = list(filter_intervals_by_mark(intervals, only_consider_marks))
    considered_intervals += len(intervals)
    intervals = list(filter_intervals_by_duration(intervals, range_min, range_max))
    matching_intervals += len(intervals)
    for interval in intervals:
      assign_interval = interval
      if assign_tier != tier:
        assign_interval = get_interval_on_tier(interval, assign_tier)
      if assign_interval.mark != assign_mark:
        assign_interval.mark = assign_mark
        changed_anything = True
        changed_intervals += 1
    grids_changed.append(changed_anything)
  return grids_changed, total_intervals, considered_intervals, matching_intervals, changed_intervals


def filter_intervals_by_mark(intervals: Iterable[Interval], marks: Set[str]) -> Generator[Interval, None, None]:
  if len(marks) == 0:
    yield from intervals
  res = (
    interval
    for interval in intervals
    if interval.mark in marks
  )
  yield from res


def filter_intervals_by_duration(intervals: Iterable[Interval], min_duration_incl: float, max_duration_excl: float) -> Generator[Interval, None, None]:
  res = (
    interval
    for interval in intervals
    if min_duration_incl <= interval.duration() < max_duration_excl
  )
  yield from res


def label_durations_core(grids: List[TextGrid], tier_name: str, assign_tier_name: str, assign_mark: str, only_consider_marks: Set[str], range_mode: Literal["percent", "percentile"], mode: Literal["separate", "all"], range_min: float, range_max: float, min_count: int) -> Tuple[List[ChangedAnything], int, int, int, int, int]:
  if mode == "all":
    return label_durations_core_all(grids, tier_name, assign_tier_name, assign_mark,
                                    only_consider_marks, range_mode, range_min, range_max, min_count)
  if mode == "separate":
    return label_durations_core_separate(grids, tier_name, assign_tier_name, assign_mark,
                                         only_consider_marks, range_mode, range_min, range_max, min_count)
  assert False
  raise NotImplementedError()


def get_percentual_boundary(durations: np.ndarray, min_val: float, max_val: float) -> Tuple[float, float]:
  max_duration = np.max(durations, axis=0)
  min_val = max_duration / 100 * min_val
  if math.isinf(max_val):
    max_val = math.inf
  else:
    max_val = max_duration / 100 * max_val
  return min_val, max_val


def get_percentile_boundary(durations: np.ndarray, min_val: float, max_val: float) -> Tuple[float, float]:
  assert 0 <= min_val < math.inf
  assert 0 < max_val
  min_val = np.percentile(durations, min_val, axis=0)
  if math.isinf(max_val):
    max_val = math.inf
  else:
    max_val = np.percentile(durations, max_val, axis=0)
  return min_val, max_val


def get_boundary(mode: Literal["percent", "percentile"], durations: np.ndarray, min_val: float, max_val: float) -> Tuple[float, float]:
  if mode == "percent":
    return get_percentual_boundary(durations, min_val, max_val)
  if mode == "percentile":
    return get_percentile_boundary(durations, min_val, max_val)
  assert False
  raise NotImplementedError()


def label_durations_core_all(grids: List[TextGrid], tier_name: str, assign_tier_name: str, assign_mark: str, only_consider_marks: Set[str], range_mode: Literal["percent", "percentile"], range_min: float, range_max: float, min_count: int) -> Tuple[List[ChangedAnything], int, int, int, int, int]:

  consider_intervals: List[List[Interval]] = []

  total_intervals = 0
  considered_intervals = 0
  for grid in grids:
    intervals = get_single_tier(grid, tier_name).intervals
    total_intervals += len(intervals)
    intervals = filter_intervals_by_mark(intervals, only_consider_marks)
    grid_consider_intervals = list(intervals)
    considered_intervals += len(grid_consider_intervals)
    consider_intervals.append(grid_consider_intervals)

  if considered_intervals < min_count:
    count_matching_intervals = 0
    grids_changed = [False for _ in grids]
    return grids_changed, total_intervals, considered_intervals, count_matching_intervals, 0, 0

  count_matching_intervals = considered_intervals

  all_interval_durations = np.array(list(
    interval.duration()
    for grid_intervals in consider_intervals
    for interval in grid_intervals
  ))

  min_val, max_val = get_boundary(range_mode, all_interval_durations, range_min, range_max)

  grids_changed = []
  changed_intervals = 0
  duration_matching_intervals = 0
  for grid, grid_intervals in zip(grids, consider_intervals):
    intervals = list(filter_intervals_by_duration(grid_intervals, min_val, max_val))
    duration_matching_intervals += len(intervals)
    assign_tier = get_single_tier(grid, assign_tier_name)
    changed_anything = False
    for interval in intervals:
      assign_interval = interval
      if assign_tier_name != tier_name:
        assign_interval = get_interval_on_tier(interval, assign_tier)
      if assign_interval.mark != assign_mark:
        assign_interval.mark = assign_mark
        changed_intervals += 1
        changed_anything = True
    grids_changed.append(changed_anything)

  return grids_changed, total_intervals, considered_intervals, count_matching_intervals, duration_matching_intervals, changed_intervals


def label_durations_core_separate(grids: List[TextGrid], tier_name: str, assign_tier_name: str, assign_mark: str, only_consider_marks: Set[str], range_mode: Literal["percent", "percentile"], range_min: float, range_max: float, min_count: int) -> Tuple[List[ChangedAnything], int, int, int, int, int]:
  assert min_count > 0
  intervals_to_marks: Dict[str, List[Interval]] = {}
  grid_indices_to_marks: Dict[str, List[int]] = {}

  total_intervals = 0
  considered_intervals = 0
  for grid_index, grid in enumerate(grids):
    intervals = get_single_tier(grid, tier_name).intervals
    total_intervals += len(intervals)
    filtered_intervals = list(filter_intervals_by_mark(intervals, only_consider_marks))
    considered_intervals += len(filtered_intervals)
    for interval in filtered_intervals:
      mark = interval.mark
      if mark not in intervals_to_marks:
        intervals_to_marks[mark] = []
        grid_indices_to_marks[mark] = []
      intervals_to_marks[mark].append(interval)
      grid_indices_to_marks[mark].append(grid_index)

  changed_intervals = 0
  count_matching_intervals = 0
  duration_matching_intervals = 0

  grids_changed = [False for _ in grids]

  for mark, mark_intervals in intervals_to_marks.items():
    if len(mark_intervals) < min_count:
      continue
    count_matching_intervals += len(mark_intervals)

    all_interval_durations = np.array(list(
      interval.duration()
      for interval in mark_intervals
    ))

    min_val, max_val = get_boundary(range_mode, all_interval_durations, range_min, range_max)

    for grid_index, interval in zip(grid_indices_to_marks[mark], mark_intervals):
      duration_match = min_val <= interval.duration() < max_val
      if duration_match:
        duration_matching_intervals += 1
        assign_interval = interval
        if assign_tier_name != tier_name:
          grid = grids[grid_index]
          assign_tier = get_single_tier(grid, assign_tier_name)
          assign_interval = get_interval_on_tier(interval, assign_tier)
        if assign_interval.mark != assign_mark:
          assign_interval.mark = assign_mark
          changed_intervals += 1
          grids_changed[grid_index] = True

  return grids_changed, total_intervals, considered_intervals, count_matching_intervals, duration_matching_intervals, changed_intervals
