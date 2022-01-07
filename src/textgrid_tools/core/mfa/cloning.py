from typing import Generator, Iterable

from textgrid.textgrid import Interval, IntervalTier


def copy_tiers(tiers: Iterable[IntervalTier], ignore_marks: bool) -> Generator[IntervalTier, None, None]:
  for tier in tiers:
    yield copy_tier(tier, ignore_marks)


def copy_tier(tier: IntervalTier, ignore_marks: bool) -> IntervalTier:
  result = IntervalTier(
    name=tier.name,
    maxTime=tier.maxTime,
    minTime=tier.minTime,
  )

  intervals = copy_intervals(tier.intervals, ignore_marks)
  result.intervals.extend(intervals)

  return result


def copy_intervals(intervals: Iterable[Interval], ignore_marks: bool) -> Generator[Interval, None, None]:
  for interval in intervals:
    yield copy_interval(interval, ignore_marks)


def copy_interval(interval: Interval, ignore_marks: bool) -> Interval:
  new_mark = "" if ignore_marks else interval.mark
  result = Interval(
    minTime=interval.minTime,
    maxTime=interval.maxTime,
    mark=new_mark,
  )
  return result
