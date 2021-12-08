from typing import Generator, Iterable, List, Optional, Set, cast

from ordered_set import OrderedSet
from textgrid.textgrid import Interval, IntervalTier, TextGrid


def tier_to_text(tier: IntervalTier, join_with: str = " ") -> str:
  words = []
  for interval in tier.intervals:
    if not interval_is_empty(interval):
      interval_text: str = interval.mark
      interval_text = interval_text.strip()
      words.append(interval_text)
  text = join_with.join(words)
  return text


def check_is_valid_grid(grid: TextGrid) -> bool:
  for tier in grid.tiers:
    tier_is_valid = check_is_valid_tier(tier)
    if not tier_is_valid:
      return False
    if tier.minTime != grid.minTime:
      return False
    if tier.maxTime != grid.maxTime:
      return False
    if grid.maxTime < tier.minTime:
      return False
  return True


def check_is_valid_tier(tier: IntervalTier) -> bool:
  # maybe check if no 0 duration intervals exist
  for i in range(1, len(tier.intervals)):
    prev_interval = cast(Interval, tier.intervals[i - 1])
    current_interval = cast(Interval, tier.intervals[i])
    if prev_interval.maxTime != current_interval.minTime:
      return False
  for interval in tier.intervals:
    if interval.minTime > interval.maxTime:
      return False
  if len(tier.intervals) > 0:
    first_interval = tier.intervals[0]
    last_interval = tier.intervals[-1]
    if tier.minTime != first_interval.minTime:
      return False
    if tier.maxTime != last_interval.maxTime:
      return False
  if tier.minTime > tier.maxTime:
    return False
  return True


def set_times_consecutively_tier(tier: IntervalTier, keep_duration: bool):
  set_times_consecutively_intervals(tier.intervals, keep_duration)

  if len(tier.intervals) > 0:
    if cast(Interval, tier.intervals[0]).minTime != tier.minTime:
      tier.minTime = cast(Interval, tier.intervals[0]).minTime

    if cast(Interval, tier.intervals[-1]).maxTime != tier.maxTime:
      tier.maxTime = cast(Interval, tier.intervals[-1]).maxTime


def set_times_consecutively_intervals(intervals: List[Interval], keep_duration: bool):
  for i in range(1, len(intervals)):
    prev_interval = cast(Interval, intervals[i - 1])
    current_interval = cast(Interval, intervals[i])
    gap_exists = current_interval.minTime != prev_interval.maxTime
    if gap_exists:
      assert prev_interval.maxTime < current_interval.minTime
      difference = current_interval.minTime - prev_interval.maxTime
      assert difference > 0
      duration = current_interval.duration()
      current_interval.minTime = prev_interval.maxTime
      if keep_duration:
        current_interval.maxTime = current_interval.minTime + duration


def get_interval_from_time(tier: IntervalTier, time: float) -> Optional[Interval]:
  for interval in cast(Iterable[Interval], tier.intervals):
    if interval.minTime <= time < interval.maxTime:
      return interval
  return None


def get_interval_from_timepoint(tier: IntervalTier, timepoint: float) -> Optional[Interval]:
  for interval in cast(Iterable[Interval], tier.intervals):
    if interval.minTime == timepoint or interval.maxTime == timepoint:
      return interval
  return None


def get_interval_from_minTime(tier: IntervalTier, minTime: float) -> Optional[Interval]:
  for interval in cast(Iterable[Interval], tier.intervals):
    if interval.minTime == minTime:
      return interval
  return None


def get_interval_from_maxTime(tier: IntervalTier, maxTime: float) -> Optional[Interval]:
  for interval in cast(Iterable[Interval], tier.intervals):
    if interval.maxTime == maxTime:
      return interval
  return None


def get_intervals_from_timespan(tier: IntervalTier, minTime: float, maxTime: float) -> Generator[Interval, None, None]:
  for interval in cast(Iterable[Interval], tier.intervals):
    if minTime <= interval.minTime and interval.maxTime <= maxTime:
      yield interval


def get_intervals_part_of_timespan(tier: IntervalTier, minTime: float, maxTime: float) -> Generator[Interval, None, None]:
  # intervals where interval.maxTime = minTime were not considered
  # intervals where interval.minTime = maxTime were not considered
  for interval in cast(Iterable[Interval], tier.intervals):
    minTime_lies_in_span = minTime <= interval.minTime and interval.minTime < maxTime
    maxTime_lies_in_span = minTime < interval.maxTime and interval.maxTime <= maxTime
    if minTime_lies_in_span or maxTime_lies_in_span:
      yield interval


def check_timepoints_exist_on_all_tiers(timepoints: List[float], tiers: List[IntervalTier]) -> bool:
  result = True
  for timepoint in timepoints:
    for tier in tiers:
      result &= check_timepoint_is_boundary_on_tier(timepoint, tier)
  return result


def check_timepoint_exist_on_all_tiers(timepoint: float, tiers: List[IntervalTier]) -> bool:
  result = True
  for tier in tiers:
    result &= check_timepoint_is_boundary_on_tier(timepoint, tier)
  return result


def check_timepoint_is_boundary_on_tier(timepoint: float, tier: IntervalTier) -> bool:
  interval = get_interval_from_timepoint(tier, timepoint)
  timepoint_exist = interval is not None
  return timepoint_exist


def get_boundary_timepoints_from_tier(tier: IntervalTier) -> OrderedSet[float]:
  return get_boundary_timepoints_from_intervals(tier.intervals)


def get_boundary_timepoints_from_intervals(intervals: List[Interval]) -> OrderedSet[float]:
  result: OrderedSet[float] = OrderedSet()
  for interval in intervals:
    result.add(interval.minTime)
    result.add(interval.maxTime)
  return result


def find_intervals_with_mark(tier: IntervalTier, marks: Set[str]) -> Generator[Interval, None, None]:
  for interval in cast(Iterable[Interval], tier.intervals):
    do_remove_interval = interval.mark in marks
    if do_remove_interval:
      yield interval


def interval_is_empty(interval: Interval) -> bool:
  return interval.mark is None or len(interval.mark.strip()) == 0

# def set_maxTime(grid: TextGrid, maxTime: float) -> None:
#   grid.maxTime = maxTime
#   for tier in grid.tiers:
#     tier.maxTime = maxTime
#     if len(tier.intervals) > 0:
#       if tier.intervals[-1].minTime >= maxTime:
#         raise Exception()
#       tier.intervals[-1].maxTime = maxTime

# def check_interval_boundaries_exist_on_all_tiers(intervals: Interval, tiers: List[IntervalTier]):
#   result = True
#   for ref_interval in intervals:
#     valid = check_boundaries_exist_on_all_tiers(ref_interval.minTime, ref_interval.maxTime, tiers)
#     if not valid:
#       result = False
#   return result


# def check_boundaries_exist_on_all_tiers(minTime: float, maxTime: float, tiers: List[IntervalTier]) -> bool:
#   result = True
#   for tier in tiers:
#     result &= check_boundaries_exist_in_tier(minTime, maxTime, tier)
#   return result


# def check_boundaries_exist_in_tier(minTime: float, maxTime: float, tier: IntervalTier) -> bool:
#   logger = getLogger(__name__)
#   corresponding_intervals = list(get_intervals_from_timespan(
#     tier, minTime, maxTime))

#   if len(corresponding_intervals) == 0:
#     logger.error(
#       f"Tier \"{tier.name}\": Interval [{minTime}, {maxTime}] does not exist!")
#     return False

#   minTime_matches = corresponding_intervals[0].minTime == minTime
#   maxTime_matches = corresponding_intervals[-1].maxTime == maxTime

#   result = True
#   if not minTime_matches:
#     logger.error(
#       f"Tier \"{tier.name}\": Start of interval [{corresponding_intervals[0].minTime}, {corresponding_intervals[0].maxTime}] (\"{corresponding_intervals[0].mark}\") does not match with start of interval [{minTime}, {maxTime}]! Difference: {corresponding_intervals[0].minTime - minTime}")
#     result = False

#   if not maxTime_matches:
#     logger.error(
#       f"Tier \"{tier.name}\": End of interval [{corresponding_intervals[-1].minTime}, {corresponding_intervals[-1].maxTime}] (\"{corresponding_intervals[-1].mark}\") does not match with end of interval [{minTime}, {maxTime}]! Difference: {corresponding_intervals[-1].maxTime - maxTime}")
#     result = False
#   return result
