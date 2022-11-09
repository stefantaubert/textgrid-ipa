from typing import Generator, Iterable, List, Optional, Set, Tuple, Union

from textgrid.textgrid import Interval, IntervalTier

from textgrid_tools.helper import get_mark, interval_is_None_or_whitespace


def merge_intervals(intervals: List[Interval], join_symbol: str, ignore_empty: bool) -> Interval:
  assert len(intervals) > 0
  marks = (get_mark(interval) for interval in intervals)
  if ignore_empty:
    marks = (m for m in marks if m != "")
  mark = join_symbol.join(marks)

  first_interval = intervals[0]
  last_interval = intervals[-1]

  interval = Interval(
    minTime=first_interval.minTime,
    maxTime=last_interval.maxTime,
    mark=mark,
  )

  return interval


def replace_intervals(tier: IntervalTier, intervals: List[Interval], replace_with: List[Interval]) -> None:
  assert len(intervals) > 0
  assert len(replace_with) > 0
  assert intervals[0].minTime == replace_with[0].minTime
  assert intervals[-1].maxTime == replace_with[-1].maxTime
  from_index = tier.intervals.index(intervals[0])
  for interval in intervals:
    tier.intervals.remove(interval)

  for interval in reversed(replace_with):
    tier.intervals.insert(from_index, interval)


def group_adjacent_pauses(intervals: Iterable[Interval]) -> Generator[Union[Interval, List[Interval]], None, None]:
  pause_group = []
  for interval in intervals:
    is_pause = interval_is_None_or_whitespace(interval)
    if is_pause:
      pause_group.append(interval)
    else:
      if len(pause_group) > 0:
        yield pause_group
        pause_group = []
      yield interval

  if len(pause_group) > 0:
    yield pause_group


def group_adjacent_intervals(intervals: Iterable[Interval], marks: Set[str]) -> Generator[Union[Interval, List[Interval]], None, None]:
  mark_group = []
  for interval in intervals:
    has_mark = interval.mark in marks
    if has_mark:
      mark_group.append(interval)
    else:
      if len(mark_group) > 0:
        yield mark_group
        mark_group = []
      yield interval

  if len(mark_group) > 0:
    yield mark_group


def group_adjacent_pauses2(intervals: Iterable[Interval]) -> Generator[Tuple[List[Interval], bool], None, None]:
  pause_group = []
  for interval in intervals:
    is_pause = interval_is_None_or_whitespace(interval)
    if is_pause:
      pause_group.append(interval)
    else:
      if len(pause_group) > 0:
        yield pause_group, True
        pause_group = []
      yield [interval], False

  if len(pause_group) > 0:
    yield pause_group, True


def group_adjacent_content_and_pauses(intervals: Iterable[Interval]) -> Generator[Tuple[List[Interval], bool], None, None]:
  current_group = []
  current_group_is_pause: Optional[bool] = None
  for interval in intervals:
    is_pause = interval_is_None_or_whitespace(interval)
    same_group = current_group_is_pause is not None and current_group_is_pause == is_pause
    if not same_group and len(current_group) > 0:
      assert current_group_is_pause is not None
      yield current_group, current_group_is_pause
      current_group = []
    current_group.append(interval)
    current_group_is_pause = is_pause

  if len(current_group) > 0:
    assert current_group_is_pause is not None
    yield current_group, current_group_is_pause
