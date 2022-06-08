from logging import Logger, getLogger
from typing import Generator, Iterable, List, Optional, Set, Tuple, cast

from textgrid.textgrid import Interval, TextGrid

from textgrid_tools.comparison import check_intervals_are_equal
from textgrid_tools.globals import ExecutionResult
from textgrid_tools.helper import (get_all_tiers, get_interval_readable, get_intervals_duration,
                                   interval_is_None_or_whitespace)
from textgrid_tools.intervals.common import merge_intervals, replace_intervals
from textgrid_tools.validation import InvalidGridError, NotExistingTierError, ValidationError


class DurationTooLowError(ValidationError):
  def __init__(self, duration: float) -> None:
    super().__init__()
    self.duration = duration

  @classmethod
  def validate(cls, duration: float):
    if not duration > 0:
      return cls(duration)
    return None

  @property
  def default_message(self) -> str:
    return f"Duration needs to be greater than zero but was \"{self.duration}\"!"


def join_intervals_on_durations(grid: TextGrid, tier_names: Set[str], join_with: str, max_duration_s: float, include_empty_intervals: bool, ignore_empty: bool, logger: Optional[Logger]) -> ExecutionResult:
  assert len(tier_names) > 0

  if logger is None:
    logger = getLogger(__name__)

  if error := InvalidGridError.validate(grid):
    return error, False

  if error := DurationTooLowError.validate(max_duration_s):
    return error, False

  for tier_name in tier_names:
    if error := NotExistingTierError.validate(grid, tier_name):
      return error, False

  tiers = list(get_all_tiers(grid, tier_names))

  changed_anything = False
  for tier in tiers:
    intervals_copy = cast(Iterable[Interval], list(tier.intervals))
    for interval in intervals_copy:
      if interval.duration() > max_duration_s:
        logger.warning(
          f"The duration of interval {get_interval_readable(interval)} ({interval.duration()}s) is bigger than {max_duration_s}!")
    # TODO fix bug
    for chunk in chunk_intervals(intervals_copy, max_duration_s, include_empty_intervals):
      merged_interval = merge_intervals(chunk, join_with, ignore_empty)
      if not check_intervals_are_equal(chunk, [merged_interval]):
        replace_intervals(tier, chunk, [merged_interval])
        changed_anything = True

  return None, changed_anything


def chunk_intervals(intervals: Iterable[Interval], max_duration_s: float, include_pauses: bool) -> Generator[List[Interval], None, None]:
  if include_pauses:
    return chunk_intervals_with_pauses(intervals, max_duration_s)
  return chunk_intervals_without_pauses(intervals, max_duration_s)


def chunk_intervals_with_pauses(intervals: Iterable[Interval], max_duration_s: float) -> Generator[List[Interval], None, None]:
  current_intervals_duration = 0
  current_intervals = []

  for interval in intervals:
    if current_intervals_duration + interval.duration() <= max_duration_s:
      current_intervals.append(interval)
      current_intervals_duration += interval.duration()
    else:
      if len(current_intervals) > 0:
        yield current_intervals
      current_intervals = [interval]
      current_intervals_duration = interval.duration()

  if len(current_intervals) > 0:
    yield current_intervals


def split_pause_at_start(intervals: List[Interval]) -> Tuple[List[Interval], List[Interval]]:
  pauses = []
  for interval in intervals:
    if interval_is_None_or_whitespace(interval):
      pauses.append(interval)
      continue
    break

  if len(pauses) < len(intervals):
    return pauses, intervals[len(pauses):]

  assert len(pauses) == len(intervals)
  return pauses, []


def split_pause_at_end(intervals: List[Interval]) -> Tuple[List[Interval], List[Interval]]:
  intervals_copy = list(reversed(intervals))
  start, content = split_pause_at_start(intervals_copy)
  end = list(reversed(start))
  content = list(reversed(content))
  return content, end


def split_pauses(intervals: List[Interval]) -> Tuple[List[Interval], List[Interval], List[Interval]]:
  start, content1 = split_pause_at_start(intervals)
  content2, end = split_pause_at_end(intervals)
  all_is_pause = len(start) == len(intervals)
  if all_is_pause:
    assert check_intervals_are_equal(start, end)
    return start, [], []
  assert check_intervals_are_equal(content1[:len(content1) - len(end)], content2[len(start):])
  start_idx = len(start)
  end_idx = len(intervals) - len(end)
  content = intervals[start_idx:end_idx]
  return start, content, end


def chunk_intervals_without_pauses(intervals: Iterable[Interval], max_duration_s: float) -> Generator[List[Interval], None, None]:
  chunks = get_duration_chunks(intervals, max_duration_s)
  return get_chunks_from_duration_chunks(chunks)


def get_chunks_from_duration_chunks(duration_chunks: Iterable[List[Interval]]) -> Generator[List[Interval], None, None]:
  for chunk in duration_chunks:
    start, content, end = split_pauses(chunk)
    for pause_interval in start:
      yield [pause_interval]
    if len(content) > 0:
      yield content
    for pause_interval in end:
      yield [pause_interval]


def get_duration_chunks(intervals: Iterable[Interval], max_duration_s: float) -> Generator[List[Interval], None, None]:
  current_intervals = []
  for interval in intervals:
    tmp_intervals = current_intervals + [interval]
    _, tmp_content, _ = split_pauses(tmp_intervals)
    tmp_content_duration = get_intervals_duration(tmp_content)
    if tmp_content_duration <= max_duration_s:
      current_intervals.append(interval)
    else:
      if len(current_intervals) > 0:
        yield current_intervals
      current_intervals = [interval]

  if len(current_intervals) > 0:
    yield current_intervals

# def split_pause_at_end(intervals: Iterable[Interval]) -> Tuple[List[Interval], List[Interval]]:
#   groups = list(group_adjacent_content_and_pauses(intervals))
#   assert len(groups) > 0
#   last_group = groups[-1]
#   last_group_is_pause = last_group[1]
#   if last_group_is_pause:
#     intervals_before_last_group = list(
#       tmp
#       for interval_group, _ in groups
#       for tmp in interval_group
#       if tmp not in last_group[0]
#     )
#     return intervals_before_last_group, last_group[0]
#   return intervals, []


# def chunk_intervals_without_pauses(intervals: Iterable[Interval], max_duration_s: float) -> Generator[List[Interval], None, None]:
#   current_intervals_duration = 0
#   current_intervals = []

#   for i, interval in enumerate(intervals):
#     is_last = i == len(intervals) - 1
#     if interval_is_None_or_whitespace(interval):
#       if len(current_intervals) == 0:
#         # do not include empty intervals as first interval in split-group
#         assert current_intervals_duration == 0
#         yield [interval]
#         continue

#     if current_intervals_duration + interval.duration() <= max_duration_s:
#       current_intervals.append(interval)
#       current_intervals_duration += interval.duration()
#     else:
#       if len(current_intervals) == 0:
#         yield [interval]
#         continue

#       content_intervals, pause_intervals = split_pause_at_end(current_intervals)
#       assert len(content_intervals) > 0
#       yield content_intervals
#       for pause_interval in pause_intervals:
#         yield pause_interval
#       current_intervals = []
#       current_intervals_duration = 0

#       if interval_is_None_or_whitespace(interval):
#         yield [interval]
#         continue

#       current_intervals.append(interval)
#       current_intervals_duration += interval.duration()

#     if is_last:
#       assert len(current_intervals) > 0
#       yield current_intervals
#       current_intervals = []
#       current_intervals_duration = 0


# def chunk_intervals_at_pauses(intervals: Iterable[Interval], max_duration_s: float) -> Generator[List[Interval], None, None]:
#   current_intervals_duration = 0
#   current_intervals = []
#   groups = list(group_adjacent_content_and_pauses(intervals))
#   for i in range(len(groups)):
#     current_group, is_pause = groups[i]
#     duration = get_intervals_duration(current_group)
#     if is_pause:
#       if len(current_intervals) == 0:
#         for pause_interval in current_group:
#           yield [pause_interval]
#         continue
#       else:
#         if current_intervals_duration + duration >= max_duration_s:
#           yield current_intervals
#           current_intervals = []
#           current_intervals_duration = 0
#           for pause_interval in current_group:
#             yield [pause_interval]
#           continue
#         else:
#           next_group_index = i + 1
#           next_group_exists = next_group_index < len(groups)
#           if next_group_exists:
#             next_group, next_group_is_pause = groups[next_group_index]
#             assert not next_group_is_pause
#             if get_intervals_duration(next_group) + current_intervals_duration + duration <= max_duration_s:
#               current_intervals.extend(current_group)
#               current_intervals_duration += get_intervals_duration(next_group)
#               continue
#           yield current_intervals
#           current_intervals = []
#           current_intervals_duration = 0
#           for pause_interval in current_group:
#             yield [pause_interval]
#           continue

#     if current_intervals_duration + duration <= max_duration_s:
#       current_intervals.extend(current_group)
#       current_intervals_duration += duration
#     else:
#       yield current_intervals
#       current_intervals = current_group.copy()
#       current_intervals_duration = duration

#   if len(current_intervals) > 0:
#     yield current_intervals
#     current_intervals = []
#     current_intervals_duration = 0
