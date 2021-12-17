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


def set_precision_grid(grid: TextGrid, ndigits: int) -> None:
  grid.minTime = round(grid.minTime, ndigits)
  grid.maxTime = round(grid.maxTime, ndigits)
  for tier in grid.tiers:
    set_precision_tier(tier, ndigits)


def set_precision_tier(tier: IntervalTier, ndigits: int) -> None:
  tier.minTime = round(tier.minTime, ndigits)
  tier.maxTime = round(tier.maxTime, ndigits)
  for interval in tier.intervals:
    set_precision_interval(interval, ndigits)


def set_precision_interval(interval: Interval, ndigits: int) -> None:
  interval.minTime = round(interval.minTime, ndigits)
  interval.maxTime = round(interval.maxTime, ndigits)


def check_is_valid_grid(grid: TextGrid) -> bool:
  if not check_minTime_and_maxTime_are_valid(grid.minTime, grid.maxTime):
    return False

  for tier in grid.tiers:
    if not do_tier_boundaries_match_those_from_grid(tier, grid):
      return False

    if not is_tier_valid(tier):
      return False
  return True


def do_tier_boundaries_match_those_from_grid(tier: IntervalTier, grid: TextGrid) -> bool:
  if tier.minTime != grid.minTime:
    return False
  if tier.maxTime != grid.maxTime:
    return False
  return True


def do_interval_boundaries_match_those_from_tier(tier: IntervalTier) -> bool:
  if len(tier.intervals) > 0:
    first_interval = tier.intervals[0]
    last_interval = tier.intervals[-1]
    if tier.minTime != first_interval.minTime:
      return False
    if tier.maxTime != last_interval.maxTime:
      return False
  return True


def check_minTime_and_maxTime_are_valid(minTime: float, maxTime: float) -> bool:
  if not (minTime < maxTime):
    return False
  if minTime < 0 or maxTime <= 0:
    return False
  return True


def is_tier_valid(tier: IntervalTier) -> bool:
  if not check_minTime_and_maxTime_are_valid(tier.minTime, tier.maxTime):
    return False

  if not check_tier_intervals_are_consecutive(tier):
    return False

  for interval in tier.intervals:
    if not check_interval_is_valid(interval):
      return False

  if not do_interval_boundaries_match_those_from_tier(tier):
    return False
  return True


def check_interval_is_valid(interval: Interval) -> bool:
  if not check_minTime_and_maxTime_are_valid(interval.minTime, interval.maxTime):
    return False


def check_tier_intervals_are_consecutive(tier: IntervalTier) -> bool:
  for i in range(1, len(tier.intervals)):
    prev_interval = cast(Interval, tier.intervals[i - 1])
    current_interval = cast(Interval, tier.intervals[i])
    if prev_interval.maxTime != current_interval.minTime:
      return False
  return True


def timepoint_is_boundary(timepoint: float, tier: IntervalTier) -> bool:
  minTime_interval = get_interval_from_minTime(tier, timepoint)
  if minTime_interval is not None:
    return True
  maxTime_interval = get_interval_from_maxTime(tier, timepoint)
  if maxTime_interval is not None:
    # it is the last interval
    return True
  return False


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


def check_timepoints_exist_on_all_tiers_as_boundaries(timepoints: List[float], tiers: List[IntervalTier]) -> bool:
  result = True
  for timepoint in timepoints:
    result &= check_timepoint_exist_on_all_tiers_as_boundary(timepoint, tiers)
  return result


def get_first_tier(grid: TextGrid, tier: str) -> IntervalTier:
  assert tier_exists(grid, tier)
  return next(get_tiers(grid, {tier}))


def tier_exists(grid: TextGrid, tier: str) -> bool:
  tiers = get_tiers(grid, {tier})
  for _ in tiers:
    return True
  return False


def get_tiers(grid: TextGrid, tiers: Set[str]) -> Generator[IntervalTier, None, None]:
  for tier in cast(Iterable[IntervalTier], grid.tiers):
    if tier.name in tiers:
      yield tier


def check_timepoint_exist_on_all_tiers_as_boundary(timepoint: float, tiers: List[IntervalTier]) -> bool:
  result = True
  for tier in tiers:
    result &= timepoint_is_boundary(timepoint, tier)
  return result


def get_boundary_timepoints_from_tier(tier: IntervalTier) -> OrderedSet[float]:
  return get_boundary_timepoints_from_intervals(tier.intervals)


def get_boundary_timepoints_from_intervals(intervals: List[Interval]) -> OrderedSet[float]:
  result: OrderedSet[float] = OrderedSet()
  for interval in intervals:
    result.add(interval.minTime)
    result.add(interval.maxTime)
  return result


def find_intervals_with_mark(tier: IntervalTier, marks: Set[str], include_empty: bool) -> Generator[Interval, None, None]:
  for interval in cast(Iterable[Interval], tier.intervals):
    match = (interval.mark in marks) or (include_empty and interval_is_empty(interval))
    if match:
      yield interval


def interval_is_empty(interval: Interval) -> bool:
  return interval.mark is None or len(interval.mark.strip()) == 0

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
